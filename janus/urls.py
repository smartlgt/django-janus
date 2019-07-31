"""janus URL Configuration
"""
from django.conf.urls import url, include
from django.utils.module_loading import import_string
from oauth2_provider.views import TokenView, RevokeTokenView

from janus import views
from janus.oauth2.views import AuthorizationView


# override profile view if django settings point to a different class
from . import app_settings as janus_app_settings
ProfileViewClass = import_string(janus_app_settings.ALLAUTH_JANUS_PROFILE_VIEW)


urlpatterns = [
    # use custom view, to enforce the user authenticate permissions
    url(r'^o/authorize/?$', AuthorizationView.as_view(), name="authorize"),

    url(r'^o/token/?$', TokenView.as_view(), name="token"),
    url(r'^o/revoke_token/?$', RevokeTokenView.as_view(), name="revoke-token"),

    url(r'^o/profile/?$', ProfileViewClass.as_view(), name="profile"),
    url(r'^o/logout/?$', views.LogoutView.as_view(), name="remote_logout"),
    url(r'^o/not_authorized/$', views.not_authorized, name="not_authorized"),

    url(r'^o/restart_authorize/$', views.restart_authorize, name="restart_authorize"),

    url('^accounts/', include('django.contrib.auth.urls')),
    url(r'', views.index, name='index'),
]
