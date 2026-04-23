async def login_generator(
        cls,
        proxy: str = None,
        api_key: str = None,
        proof_token: str = None,
        cookies: Cookies = None,
        headers: dict = None,
        **kwargs
    ) -> AsyncIterator:
        if cls._expires is not None and (cls._expires - 60 * 10) < time.time():
            cls._headers = cls._api_key = None
        if cls._headers is None or headers is not None:
            cls._headers = {} if headers is None else headers
        if proof_token is not None:
            cls.request_config.proof_token = proof_token
        if cookies is not None:
            cls.request_config.cookies = cookies
        if api_key is not None:
            cls._create_request_args(cls.request_config.cookies, cls.request_config.headers)
            cls._set_api_key(api_key)
        else:
            try:
                cls.request_config = await get_request_config(cls.request_config, proxy)
                if cls.request_config is None:
                    cls.request_config = RequestConfig()
                cls._create_request_args(cls.request_config.cookies, cls.request_config.headers)
                if cls.needs_auth and cls.request_config.access_token is None:
                    raise NoValidHarFileError(f"Missing access token")
                if not cls._set_api_key(cls.request_config.access_token):
                    raise NoValidHarFileError(f"Access token is not valid: {cls.request_config.access_token}")
            except NoValidHarFileError:
                if has_nodriver:
                    if cls.request_config.access_token is None:
                        yield RequestLogin(cls.label, os.environ.get("G4F_LOGIN_URL", ""))
                        await cls.nodriver_auth(proxy)
                else:
                    raise