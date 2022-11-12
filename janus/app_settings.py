from django.conf import settings

ALLAUTH_JANUS_PROFILE_VIEW = getattr(settings, 'ALLAUTH_JANUS_PROFILE_VIEW', 'janus.views.ProfileView')

ALLAUTH_JANUS_ADMIN_CLASS = getattr(settings, 'ALLAUTH_JANUS_ADMIN_CLASS', 'janus.admin.JanusUserAdmin')

# Enable OIDC only if it is enabled in django-oauth-toolkit.
OAUTH_SETTINGS = getattr(settings, 'OAUTH2_PROVIDER', {})
JANUS_OIDC_ENABLED = OAUTH_SETTINGS.get('OIDC_ENABLED', False)

# janus supports some non-standard claims. Set which scope is required to return the claims.
JANUS_OIDC_SCOPE_EXTRA = getattr(settings, 'JANUS_OIDC_SCOPE_EXTRA', 'janus')
