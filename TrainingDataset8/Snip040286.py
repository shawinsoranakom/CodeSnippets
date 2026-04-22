def get_app(self) -> tornado.web.Application:
        return tornado.web.Application(
            [(f"{MOCK_ENDPOINT}/(.*)", MediaFileHandler, {"path": ""})]
        )