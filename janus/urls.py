"""janus URL Configuration
"""
from django.conf.urls import url, include
from oauth2_provider.views import TokenView, RevokeTokenView

from janus import views
from janus.oauth2.views import AuthorizationView

urlpatterns = [
    # use custom view, to enforce the user authenticate permissions
    url(r'^o/authorize/?$', AuthorizationView.as_view(), name="authorize"),

    url(r'^o/token/?$', TokenView.as_view(), name="token"),
    url(r'^o/revoke_token/?$', RevokeTokenView.as_view(), name="revoke-token"),

    url(r'^o/profile/?$', views.ProfileView.as_view(), name="profile"),
    url(r'^o/not_authorized/$', views.not_authorized, name="not_authorized"),

    url(r'^o/restart_authorize/$', views.restart_authorize, name="restart_authorize"),

    url('^accounts/', include('django.contrib.auth.urls')),
    url(r'', views.index, name='index'),
]
