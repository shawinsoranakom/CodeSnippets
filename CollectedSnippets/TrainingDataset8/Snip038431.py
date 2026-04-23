async def get(self):
        ok, msg = await self._callback()
        if ok:
            self.write(msg)
            self.set_status(200)

            # Tornado will set the _xsrf cookie automatically for the page on
            # request for the document. However, if the server is reset and
            # server.enableXsrfProtection is updated, the browser does not reload the document.
            # Manually setting the cookie on /healthz since it is pinged when the
            # browser is disconnected from the server.
            if config.get_option("server.enableXsrfProtection"):
                self.set_cookie("_xsrf", self.xsrf_token)

        else:
            # 503 = SERVICE_UNAVAILABLE
            self.set_status(503)
            self.write(msg)