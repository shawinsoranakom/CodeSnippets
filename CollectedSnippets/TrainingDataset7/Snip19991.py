def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # This is a list of the cookie values passed to set_cookie() over
        # the course of the request-response.
        self._cookies_set = []