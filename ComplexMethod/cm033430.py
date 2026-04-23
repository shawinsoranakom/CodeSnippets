async def wrapper(*args, **kwargs):
        # Validate the token (API Key)
        if os.environ.get("DISABLE_SDK"):
            err = WerkzeugUnauthorized(description="`Authorization` can't be empty")
            err.code = RetCode.SUCCESS
            raise err

        authorization_str = request.headers.get("Authorization")
        if not authorization_str:
            err = WerkzeugUnauthorized(description="`Authorization` can't be empty")
            err.code = RetCode.SUCCESS
            raise err

        authorization_list = authorization_str.split()
        if len(authorization_list) < 2:
            err = WerkzeugUnauthorized(description="Please check your authorization format.")
            err.code = RetCode.AUTHENTICATION_ERROR
            raise err

        token = authorization_list[1]

        # First try API token (explicit API token authentication)
        objs = APIToken.query(token=token)
        if objs:
            # On success, inject tenant_id into the route function's kwargs
            kwargs["tenant_id"] = objs[0].tenant_id
            result = func(*args, **kwargs)
            if inspect.iscoroutine(result):
                return await result
            return result

        # Fallback: try login token (for clients that use login token as API token)
        # Login tokens are JWT-encoded (URLSafeTimedSerializer), need to decode to get raw access_token
        from api.db.services.user_service import UserService
        from common.constants import StatusEnum
        from common import settings
        from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
        try:
            jwt = Serializer(secret_key=settings.SECRET_KEY)
            raw_token = str(jwt.loads(token))
            user = UserService.query(access_token=raw_token, status=StatusEnum.VALID.value)
            if user:
                # On success, inject tenant_id from user's tenant
                from api.db.services.user_service import UserTenantService
                tenants = UserTenantService.query(user_id=user[0].id)
                if tenants:
                    kwargs["tenant_id"] = tenants[0].tenant_id
                    result = func(*args, **kwargs)
                    if inspect.iscoroutine(result):
                        return await result
                    return result
        except Exception:
            pass

        err = WerkzeugUnauthorized(description="Authentication error: API key is invalid!")
        err.code = RetCode.AUTHENTICATION_ERROR
        raise err