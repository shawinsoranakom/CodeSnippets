async def _api_key_security_impl(
        self,
        query_param: str | None,
        header_param: str | None,
        db: AsyncSession,
        settings_service,
    ) -> UserRead | None:
        result: ApiKey | User | None

        if settings_service.auth_settings.AUTO_LOGIN:
            if not settings_service.auth_settings.SUPERUSER:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing first superuser credentials",
                )
            if not query_param and not header_param:
                if settings_service.auth_settings.skip_auth_auto_login:
                    result = await get_user_by_username(db, settings_service.auth_settings.SUPERUSER)
                    logger.warning(AUTO_LOGIN_WARNING)
                    return UserRead.model_validate(result, from_attributes=True)
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=AUTO_LOGIN_ERROR,
                )
            # At this point, at least one of query_param or header_param is truthy
            api_key = query_param or header_param
            if api_key is None:  # pragma: no cover - guaranteed by the if-condition above
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing API key")
            result = await check_key(db, api_key)

        elif not query_param and not header_param:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="An API key must be passed as query or header",
            )

        else:
            # At least one of query_param or header_param is truthy
            api_key = query_param or header_param
            if api_key is None:  # pragma: no cover - guaranteed by the elif-condition above
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing API key")
            result = await check_key(db, api_key)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing API key",
            )

        if isinstance(result, User):
            return UserRead.model_validate(result, from_attributes=True)

        msg = "Invalid result type"
        raise ValueError(msg)