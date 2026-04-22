async def get(self) -> None:
        ok, msg = await self._callback()

        if ok:
            # ALLOWED_MESSAGE_ORIGINS must be wrapped in a dictionary because Tornado
            # disallows writing lists directly into responses due to potential XSS
            # vulnerabilities.
            # See https://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler.write
            self.write({"allowedOrigins": ALLOWED_MESSAGE_ORIGINS})
            self.set_status(200)

            if config.get_option("server.enableXsrfProtection"):
                self.set_cookie("_xsrf", self.xsrf_token)

        else:
            # 503 = SERVICE_UNAVAILABLE
            self.set_status(503)
            self.write(msg)