async def asession(self):
        engine = import_module(settings.SESSION_ENGINE)
        cookie = self.cookies.get(settings.SESSION_COOKIE_NAME)
        if cookie:
            return engine.SessionStore(cookie.value)
        session = engine.SessionStore()
        await session.asave()
        self.cookies[settings.SESSION_COOKIE_NAME] = session.session_key
        return session