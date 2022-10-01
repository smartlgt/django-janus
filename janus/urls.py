from django.conf.urls import include
from django.urls import path, re_path
from django.utils.module_loading import import_string
from oauth2_provider.views import TokenView, RevokeTokenView, IntrospectTokenView

from janus import views
from janus.oauth2.views import AuthorizationView


# override profile view if django settings point to a different class
from . import app_settings as janus_app_settings
ProfileViewClass = import_string(janus_app_settings.ALLAUTH_JANUS_PROFILE_VIEW)


urlpatterns = [
    # use custom view, to enforce the user authenticate permissions
    re_path(r'^o/authorize/?$', AuthorizationView.as_view(), name="authorize"),

    # default oauth2_provider.url.base_urlpatterns
    re_path(r'^o/token/?$', TokenView.as_view(), name="token"),
    re_path(r'^o/revoke_token/?$', RevokeTokenView.as_view(), name="revoke-token"),
    re_path(r"^introspect/?$", IntrospectTokenView.as_view(), name="introspect"),

    # custom urls
    re_path(r'^o/profile/?$', ProfileViewClass.as_view(), name="profile"),
    re_path(r'^o/logout/?$', views.LogoutView.as_view(), name="remote_logout"),
    re_path(r'^o/not_authorized/$', views.not_authorized, name="not_authorized"),

    re_path(r'^o/restart_authorize/$', views.restart_authorize, name="restart_authorize"),

    path('accounts/', include('django.contrib.auth.urls')),
    path('', views.index, name='index'),
]
