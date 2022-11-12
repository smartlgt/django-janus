from allauth.account.models import EmailAddress
from oauth2_provider.oauth2_validators import OAuth2Validator

from janus import app_settings
from janus.oauth2.util import get_permissions, get_group_list


class JanusOAuth2Validator(OAuth2Validator):
    # As per 5.4 of the OIDC Core Specs the OIDC Scopes are used to determine which claims are returned.
    # See https://openid.net/specs/openid-connect-core-1_0.html#ScopeClaims
    # Update with additional non-standard claims we support.
    oidc_claim_scope = OAuth2Validator.oidc_claim_scope
    oidc_claim_scope.update({"is_staff": app_settings.JANUS_OIDC_SCOPE_EXTRA,
                             "is_superuser": app_settings.JANUS_OIDC_SCOPE_EXTRA,
                             "can_authenticate": app_settings.JANUS_OIDC_SCOPE_EXTRA,
                             "groups": app_settings.JANUS_OIDC_SCOPE_EXTRA
                             })

    def get_additional_claims(self, request):
        # The default implementation only returns very little data.
        # Return the data for the additional claims that we want support.

        user = request.user

        can_authenticate, is_staff, is_superuser = get_permissions(user, request.client)

        # The `sub` claim is a unique id for a user. The `sub` claim is always returned.
        return {
            "name": ' '.join([user.first_name, user.last_name]),
            "given_name": user.first_name,
            "family_name": user.last_name,
            "preferred_username": user.username,
            "email": user.email,
            "email_verified": EmailAddress.objects.filter(user=user, verified=True).exists(),
            "is_staff": is_staff,
            "is_superuser": is_superuser,
            # TODO: Is `can_authenticate` required?
            "can_authenticate": can_authenticate,
            "groups": get_group_list(user, request.client),
        }

    def get_discovery_claims(self, request):
        # Used for discovery of the available claims at the Auto Discovery Endpoint.
        return ["name", "given_name", "family_name", "preferred_username", "email", "email_verified", "is_staff",
                "is_superuser", "can_authenticate", "groups"]
