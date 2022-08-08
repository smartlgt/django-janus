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

from janus.models import ProfileGroup, Profile, GroupPermission, ProfilePermission, \
    ApplicationExtension


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

    def get_profile_memberships(self, user):

        all_profiles = Profile.objects.get(user=user).group.all()

        # add the default groups by default
        default_profile = ProfileGroup.objects.filter(default=True)
        all_profiles = set(all_profiles | default_profile)

        return list(all_profiles)

    def get_group_permissions(self, user, application):
        """
        Validates the group permissions for a user given a token
        :param user:
        :param token:
        :return:
        """
        is_staff = False
        is_superuser = False
        can_authenticate = False

        if not user.is_authenticated:
            return can_authenticate, is_staff, is_superuser

        all_groups = self.get_profile_memberships(user)

        for g in all_groups:
            gp = GroupPermission.objects.filter(profile_group=g, application=application)
            if gp.count() == 0:
                continue
            elif gp.count() == 1:
                gp = gp.first()
                can_authenticate = gp.can_authenticate
                is_staff = gp.is_staff
                is_superuser = gp.is_superuser
            else:
                print('We have a problem')
        return can_authenticate, is_staff, is_superuser

    def get_personal_permissions(self, user, application):
        """
        Validates the personal permissions for a user given a token
        :param user:
        :param token:
        :return:
        """
        is_staff = None
        is_superuser = None
        can_authenticate = None
        if not user.is_authenticated:
            return can_authenticate, is_staff, is_superuser

        pp = ProfilePermission.objects.filter(profile__user=user, application=application).first()
        if pp:
            is_staff = True if pp.is_staff else None
            is_superuser = True if pp.is_superuser else None
            can_authenticate = True if pp.can_authenticate else None
        return can_authenticate, is_staff, is_superuser


    def get_profile_group_memberships(self, user, application):
        """
        collect group names form user profile group memberships
        :param user:
        :param token:
        :return:
        """

        all_profiles = self.get_profile_memberships(user)

        group_list = set()

        for g in all_profiles:
            # get profile-group-permission object
            gp = GroupPermission.objects.filter(profile_group=g, application=application)
            for elem in gp:
                groups = elem.groups.all()

                for g in groups:
                    # ensure only groups for this application can be returned
                    if g.application == application:
                        group_list.add(g.name)

        return group_list


    def get_profile_personal_memberships(self, user, application):
        """
        collect group names form user profile permission
        :param user:
        :param token:
        :return:
        """

        profile_permissions = ProfilePermission.objects.filter(profile__user=user, application=application).first()

        group_list = set()

        if profile_permissions:
            groups = profile_permissions.groups.all()

            for g in groups:
                # ensure only groups for this application can be returned
                if g.application == application:
                    group_list.add(g.name)

        return group_list

    def get_permissions(self, user, application):
        """
        return permissions according to application settings, personal overwrite and default values
        :param user:
        :param application:
        :return:
        """
        can_authenticate, is_staff, is_superuser = self.get_group_permissions(user, application)

        # if set the personal settings overwrite the user settings
        pp_authenticate, pp_staff, pp_superuser = self.get_personal_permissions(user, application)
        if pp_staff is not None:
            is_staff = pp_staff

        if pp_superuser is not None:
            is_superuser = pp_superuser

        if pp_authenticate is not None:
            can_authenticate = pp_authenticate

        return can_authenticate, is_staff, is_superuser


    def get_group_list(self, user, application):

        groups = set()
        groups = groups.union(self.get_profile_group_memberships(user, application))
        groups = groups.union(self.get_profile_personal_memberships(user, application))

        return list(groups)


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

        can_authenticate, is_staff, is_superuser = self.get_permissions(user, application)

        groups = self.get_group_list(user, application)

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
