def get_app(self):
        ComponentRegistry._instance = None
        return tornado.web.Application(
            [
                (
                    "/component/(.*)",
                    ComponentRequestHandler,
                    dict(registry=ComponentRegistry.instance()),
                )
            ]
        )