async def _alogin(self, user, backend=None):
        from django.contrib.auth import alogin

        # Create a fake request to store login details.
        request = HttpRequest()
        session = await self.asession()
        if session:
            request.session = session
        else:
            engine = import_module(settings.SESSION_ENGINE)
            request.session = engine.SessionStore()

        await alogin(request, user, backend)
        # Save the session values.
        await request.session.asave()
        self._set_login_cookies(request)