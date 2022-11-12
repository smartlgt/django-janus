from django.contrib.sessions.models import Session
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views import View
from oauth2_provider.exceptions import OAuthToolkitError
from oauth2_provider.models import AccessToken, RefreshToken
from oauth2_provider.views import ProtectedResourceView
import json

from janus.oauth2.util import get_permissions, get_group_list


class LogoutView(View):
    def get(self, request):
        access_token = request.GET.get('access_token', None)
        if not access_token:
            access_token = request.META.get('HTTP_AUTHORIZATION', None)
            if access_token:
                access_token = access_token.replace("Bearer ", "")

        token = AccessToken.objects.filter(token=access_token).first()

        if not token:
            return self.error_response(OAuthToolkitError("No access token"))

        # dont check for expired/valid, if the token was valid it's enough
        #if not token.is_valid():
        #    return self.error_response(OAuthToolkitError("invalid access token"))

        user = token.user

        self.clean_user_sessions(user)
        self.clean_user_tokens(user)

        return HttpResponse("OK")

    def clean_user_sessions(self, user):
        now = timezone.now()
        sessions = Session.objects.filter(expire_date__gt=now)

        user_id2 = str(user.id)
        for session in sessions:
            user_id = session.get_decoded().get('_auth_user_id')
            if user_id == user_id2:
                session.delete()

    def clean_user_tokens(self, user):
        AccessToken.objects.filter(user=user).delete()
        RefreshToken.objects.filter(user=user).delete()


class ProfileView(ProtectedResourceView):

    def get(self, request):
        if request.resource_owner:
            user = request.resource_owner

            # set = user.accesstoken_set.all()
            access_token = request.GET.get('access_token', None)
            if not access_token:
                access_token = request.META.get('HTTP_AUTHORIZATION', None)
                if access_token:
                    access_token = access_token.replace("Bearer ", "")

            token = AccessToken.objects.filter(token=access_token).first()

            if not token:
                return self.error_response(OAuthToolkitError("No access token"))

            if not token.is_valid():
                return self.error_response(OAuthToolkitError("invalid access token"))

            user = token.user
            application = token.application

            data = self.generate_json_data(user, application)
            data = self._replace_keys_by_application(data, application)

            return JsonResponse(data)

        return self.error_response(OAuthToolkitError("No resource owner"))


    def generate_json_data(self, user, application):
        """
        generate the profile response json object
        :param user:
        :param application:
        :return:
        """

        can_authenticate, is_staff, is_superuser = get_permissions(user, application)

        groups = get_group_list(user, application)

        data = {
            'id': user.username,
            'internal_id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'name': user.first_name + ' ' + user.last_name,
            'email': user.email,
            # ToDo: check the emails
            'email_verified': True,
            'is_staff': is_staff,
            'is_superuser': is_superuser,
            'can_authenticate': can_authenticate,
            'groups': groups,
        }

        return data

    @staticmethod
    def _replace_keys_by_application(json_data, application):
        """
        replace json keys, according to the given replacement dic from the ApplicationExtension database model
        :param json_data: json dict
        :param application: allauth application
        :return: processed json dict
        """
        try:
            extension = application.extension
            replacement_mapping = extension.profile_replace_json
        except ObjectDoesNotExist:
            return json_data
        if replacement_mapping is not None:
            # iterate over replacements and apply them
            replace_data = json.loads(replacement_mapping)
            for key, value in replace_data.items():
                if key in json_data:
                    json_data[value] = json_data.pop(key)
        return json_data


def index(request):

    args = {
    }

    return render(request, 'pages/index.html', args)


def not_authorized(request):
    return HttpResponse("Sorry, you are not authorized to access this application."
                        " Contact an admin if you think this is a mistake.")


def restart_authorize(request):
    url = request.session.get('requested_path', None)
    if url:
        try:
            del request.session['requested_path']
        except KeyError:
            pass
        return redirect(url)

    return redirect('/')
