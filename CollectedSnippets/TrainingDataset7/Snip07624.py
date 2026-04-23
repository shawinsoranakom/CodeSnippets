def __init__(self, request, *args, **kwargs):
        if not hasattr(request, "session"):
            raise ImproperlyConfigured(
                "The session-based temporary message storage requires session "
                "middleware to be installed, and come before the message "
                "middleware in the MIDDLEWARE list."
            )
        super().__init__(request, *args, **kwargs)