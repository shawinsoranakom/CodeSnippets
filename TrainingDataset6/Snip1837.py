async def __call__(self, request: Request) -> str | None:
        authorization = request.headers.get("Authorization")
        if not authorization:
            if self.auto_error:
                raise self.make_not_authenticated_error()
            else:
                return None
        return authorization