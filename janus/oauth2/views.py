import urllib

import allauth
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.shortcuts import redirect
from oauth2_provider.models import get_application_model
from oauth2_provider.views import AuthorizationView

from janus.models import ProfilePermission


def authentication_permitted(user, application):
    permitted = False

    # check if a override entry (ProfilePermission) exists
    slinge_permit = ProfilePermission.objects.filter(profile=user.profile, application=application)
    if len(slinge_permit) == 1:
        return slinge_permit[0].can_authenticate

    # check if user can autenticate for this app
    for group in user.profile.group.all():
        permits = group.grouppermission_set.filter(application=application).all()
        for permit in permits:
            if permit.can_authenticate:
                permitted = True

    if not permitted:
        return False
    return True


class AuthorizationView(AuthorizationView):

    # override the get request class, so we can deny the access before the validation starts
    def get(self, request, *args, **kwargs):
        user = request.user
        application = get_application_model().objects.get(client_id=request.GET.get('client_id'))

        permitted = authentication_permitted(user, application)

        if permitted:

            # check if the application needs a valid email address
            required = False
            if hasattr(application, 'applicationextension'):
                required = application.applicationextension and application.applicationextension.email_required

            if required:

                # check if the user has a email address (else redirect to form)
                if user.email:

                # check if the email address is verified (else redirect to verification page)
                    verified = EmailAddress.objects.filter(user=user, verified=True).exists()

                    if verified:
                        return super(AuthorizationView, self).get(request, *args, **kwargs)
                    else:
                        send_email_confirmation(request, request.user)
                        if request.GET:
                            params = urllib.parse.urlencode(request.GET)
                            request.session['requested_path'] = request.path + '?' + params
                        return redirect('account_email_verification_sent')

                else:
                    if request.GET:
                        params = urllib.parse.urlencode(request.GET)
                        request.session['requested_path'] = request.path + '?' + params
                    return redirect('account_email')


            return super(AuthorizationView, self).get(request, *args, **kwargs)
        else:
            return redirect('not_authorized')
