def get_app(self):
        return tornado.web.Application(
            [(r"/healthz", HealthHandler, dict(callback=self.is_healthy))]
        )