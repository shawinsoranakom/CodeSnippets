async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        api_key: str = None,
        cookies: list = None,
        base_url: str = base_url,
        **kwargs
    ) -> AsyncResult:
        api_key = os.environ.get("CLAUDE_COOKIE", api_key)
        cookies = cookies or get_cookies(cls.cookie_domain)
        if not api_key:
            api_key = "; ".join([f"{key}={value}" for key, value in cookies.items()])
        if not api_key:
            raise MissingAuthError("Claude cookie not found. Please set the 'CLAUDE_COOKIE' environment variable.")
        if not cls.organization_id:
            cls.organization_id = os.environ.get("CLAUDE_ORGANIZATION_ID")
            if not cls.organization_id:
                cls.organization_id = cookies.get("lastActiveOrg")
            if not cls.organization_id:
                raise MissingAuthError("Claude organization ID not found. Please set the 'CLAUDE_ORGANIZATION_ID' environment variable.")
        async for chunk in super().create_async_generator(
            model=model,
            messages=messages,
            base_url=f"{base_url}/{cls.organization_id}",
            headers={"cookie": api_key},
            **kwargs
        ):
            yield chunk