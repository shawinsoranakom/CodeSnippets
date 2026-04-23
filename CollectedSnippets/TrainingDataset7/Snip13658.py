async def alogout(self):
        """See logout()."""
        from django.contrib.auth import aget_user, alogout

        request = HttpRequest()
        session = await self.asession()
        if session:
            request.session = session
            request.user = await aget_user(request)
        else:
            engine = import_module(settings.SESSION_ENGINE)
            request.session = engine.SessionStore()
        await alogout(request)
        self.cookies = SimpleCookie()