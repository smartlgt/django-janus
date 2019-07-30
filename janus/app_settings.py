from django.conf import settings

ALLAUTH_JANUS_PROFILE_VIEW = getattr(settings, 'ALLAUTH_JANUS_PROFILE_VIEW', 'janus.views.ProfileView')

ALLAUTH_JANUS_ADMIN_CLASS = getattr(settings, 'ALLAUTH_JANUS_ADMIN_CLASS', 'janus.admin.JanusUserAdmin')
