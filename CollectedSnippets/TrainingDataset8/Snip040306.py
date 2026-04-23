def get_app(self):
        return tornado.web.Application(
            [
                (
                    r"/st-allowed-message-origins",
                    AllowedMessageOriginsHandler,
                    dict(callback=self.is_healthy),
                )
            ]
        )