from janus.models import Profile


class ProfileMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        if request.user.is_authenticated:
            if not hasattr(request.user, 'profile'):
                Profile.create_default_profile(request.user)

        return response