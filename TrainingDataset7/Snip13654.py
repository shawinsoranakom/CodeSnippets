def _login(self, user, backend=None):
        from django.contrib.auth import login

        # Create a fake request to store login details.
        request = HttpRequest()
        if self.session:
            request.session = self.session
        else:
            engine = import_module(settings.SESSION_ENGINE)
            request.session = engine.SessionStore()
        login(request, user, backend)
        # Save the session values.
        request.session.save()
        self._set_login_cookies(request)