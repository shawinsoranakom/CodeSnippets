def __init__(
        self,
        name: str,
        path: Optional[str] = None,
        url: Optional[str] = None,
    ):
        if (path is None and url is None) or (path is not None and url is not None):
            raise StreamlitAPIException(
                "Either 'path' or 'url' must be set, but not both."
            )

        self.name = name
        self.path = path
        self.url = url