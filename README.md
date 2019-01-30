# setup

## installation

`pip install git+https://github.com/smartlgt/django-janus#egg=janus`

## settings.py

add to installed apps:

```
INSTALLED_APPS = [
    # other apps
    
    #optional ldap auth
    'django_python3_ldap',
    
    'django.contrib.sites',
    'oauth2_provider',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'janus',
    
]
```

Set a fix site ID or init the database table via manage commands:
```
SITE_ID = 1
```

Oauth config & cors:
```
OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'

CORS_ORIGIN_ALLOW_ALL = False
```


its possible to use any social login, reffer the allauth docs for configuration.
Allauth config e.G.:
```
ACCOUNT_EMAIL_REQUIRED = False
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_AUTHENTICATION_METHOD = "username"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = 'restart_authorize'
ACCOUNT_LOGOUT_ON_GET = True
```

E-Mail config e.G.:
```
EMAIL_USE_SSL = True
EMAIL_HOST = 'smtp.example.com'
EMAIL_HOST_USER = 'mail@example.com'
EMAIL_HOST_PASSWORD = '********'
EMAIL_PORT = 465
DEFAULT_FROM_EMAIL = 'name <mail@example.com>'

```

(optional) setup your ldap server
```
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

```
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('oauth2/', include('janus.urls')),
]
```


## first run
migrate your database
```
./manage.py migrate
```

if you open a browser and look at the index page you should see `Hello from janus` on your screen.


# usage

## endpoints
### o/authorize/
OAuth2 authorize endpoint

### o/token/
OAuth2 access token endpoint

### o/revoke_token/
OAuth2 revoke access or refresh tokens

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
  "can_authenticate": "True"
}
````

## configuration
- navigate to `/admin/` to setup the OAuth2 uids and secrets.