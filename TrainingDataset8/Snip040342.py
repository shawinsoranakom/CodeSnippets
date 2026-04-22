def get_app(self) -> tornado.web.Application:
        self.server = Server(
            "/not/a/script.py",
            "test command line",
        )
        app = self.server._create_app()
        return app