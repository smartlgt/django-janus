# setup

django-janus is an [OAuth2](https://www.rfc-editor.org/rfc/rfc6749) authorization server.
The [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html) and [Discovery 1.0](https://openid.net/specs/openid-connect-discovery-1_0.html) Standards are implemented.

## installation

`pip install git+https://github.com/smartlgt/django-janus#egg=django-janus`

## settings.py

add to installed apps:

```python3
INSTALLED_APPS = [
    # other apps
    
    #optional ldap auth
    'django_python3_ldap',
    
    'django.contrib.sites',
    'corsheaders',
    'oauth2_provider',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'janus',
    
]
```

Set a fix site ID or init the database table via manage commands:
```python3
SITE_ID = 1
```

Oauth config:
```python3
OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'
```

cors for web apps:
```python3
MIDDLEWARE = (
    # ...
    'corsheaders.middleware.CorsMiddleware',
    # ...
)


CORS_ORIGIN_ALLOW_ALL = True
// now limit the allow all to the following path:
CORS_URLS_REGEX = r"^/oauth2/.*$"

```


its possible to use any social login, reffer the allauth docs for configuration.
Allauth config e.G.:
```python3
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_AUTHENTICATION_METHOD = "username"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = 'restart_authorize'
ACCOUNT_LOGOUT_ON_GET = True
```

E-Mail config e.G.:
```python3
EMAIL_USE_SSL = True
EMAIL_HOST = 'smtp.example.com'
EMAIL_HOST_USER = 'mail@example.com'
EMAIL_HOST_PASSWORD = '********'
EMAIL_PORT = 465
DEFAULT_FROM_EMAIL = 'name <mail@example.com>'

```

(recommended) cleanup old token
```python3
CELERY_BEAT_SCHEDULE = {
    'cleanup_token': {
        'task': 'janus.tasks.cleanup_token',
        'schedule': crontab(minute='1', hour='6')
    },
}
```

(optional) enable and configure OIDC
<!-- TODO: the meaning of the custom claims should probably be documented in more detail. -->
```python3
# Scope in which additional claims are included. These claims are is_staff, is_superuser and groups.
JANUS_OIDC_SCOPE_EXTRA = "profile" 
OAUTH2_PROVIDER = {
    "OIDC_ENABLED": True, # Enable OIDC
    "OIDC_ISS_ENDPOINT": "[...]",
    "OAUTH2_VALIDATOR_CLASS": "janus.oauth2.validator.JanusOAuth2Validator",
    "OIDC_RSA_PRIVATE_KEY": "[...]", # Generate with `openssl genrsa -out oidc.key 4096`
    "SCOPES": { # Claims are returned based on granted scopes. See OIDC Core section 5.4.
        "openid": "Connect with your Account",
        "profile": "Access your Name and Username",
        "email": "Access your Mail-Address",
    }
}
```

(optional) setup your ldap server
```python3
# The URL of the LDAP server.
LDAP_AUTH_URL = "ldap.exmaple.com"

# Initiate TLS on connection.
LDAP_AUTH_USE_TLS = True

# The LDAP search base for looking up users.
LDAP_AUTH_SEARCH_BASE = "OU=people,DC=example,DC=com"

# The LDAP class that represents a user.
LDAP_AUTH_OBJECT_CLASS = "inetOrgPerson"

# A tuple of django model fields used to uniquely identify a user.
LDAP_AUTH_USER_LOOKUP_FIELDS = ("username",)

# 
LDAP_AUTH_SYNC_PERMISSIONS = False

# define auth order
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # try model auth first
    'django_python3_ldap.auth.LDAPBackend', # "fallback" to ldap authentifiaction
)
```

## urls.py

```python3
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('oauth2/', include('janus.urls')),
]
```


## first run
migrate your database
```bash
./manage.py migrate
```

if you open a browser and look at the index page you should see `Hello from janus` on your screen.


# usage

## OAuth2 endpoints
### o/authorize/
OAuth2 authorize endpoint

### o/token/
OAuth2 access token endpoint

### o/revoke_token/
OAuth2 revoke access or refresh tokens

### o/introspect/
OAuth2 introspection endpoint. Requires `introspect` scope.

### o/profile/
custom profile endpoint, returns user profile information as json:
````json
{
  "id": "some_username",
  "first_name": "Jon",
  "last_name": "Doe",
  "name": "Jon Doe",
  "email": "mail@example.com",
  "email_verified": "True",
  "is_superuser": "False",
  "can_authenticate": "True",
  "groups": ["staff", "customer"]
}
````

#### extend profile response
overwrite settings like this:
`ALLAUTH_JANUS_PROFILE_VIEW = 'app.views.ProfileViewCustom'`

add a new profie view class and customize as needed
```python3
from janus.views import ProfileView
class ProfileViewCustom(ProfileView):

    def generate_json_data(self, user, application):
        data = super().generate_json_data(user, application)
        data['custom_values'] = user.custom_user_value
        return data
```

## OIDC endpoints
### `o/userinfo/`
UserInfo endpoint as per section 5.3 of OpenID Connect Core 1.0.

### `o/.well-known/openid-configuration/`
OpenID Provider Configuration endpoint as per section 4 of OpenID Connect Discovery 1.0.

### `o/.well-known/jwks.json`
JSON Web Key Set endpoint as per section 3 of OpenID Connect Discovery 1.0.

## admin custom user class
set `ALLAUTH_JANUS_ADMIN_CLASS = 'app.admin_custom.CustomUserAdmin'`

```python3
from janus.admin import JanusUserAdmin
class CustomUserAdmin(JanusUserAdmin):

    fieldsets = JanusUserAdmin.fieldsets + (
        ("Custom Area", {'fields': ('some_field',)}),
    )
```

## configuration
- navigate to `/admin/` to setup the OAuth2 uids and secrets.

### setup a profile group and add permissions
setup your first group, eg. default and set the default flag.
all new user will be added to the default flag. for testing, you may need to add the default group for the first admin user by hand.

as a second step you need to authorize your app by mapping a "Can authenticate" flag between the application and the new default group.
see Group permissions for that.

you can also add a single permission for a user without the need of generating groups. see: Profile permissions

there is an option to provide Application groups for a application based on profiles or group permission these groups get returned to the application on the profile call.