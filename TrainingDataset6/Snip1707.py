def __init__(
        self, app: ASGIApp, context_name: str = "fastapi_middleware_astack"
    ) -> None:
        self.app = app
        self.context_name = context_name