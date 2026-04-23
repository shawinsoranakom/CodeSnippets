async def get_current_user_mcp(
        self,
        token: str | Coroutine | None,
        query_param: str | None,
        header_param: str | None,
        db: AsyncSession,
    ) -> User | UserRead:
        if token:
            return await self.get_current_user_from_access_token(token, db)

        settings_service = self.settings
        result: ApiKey | User | None

        if settings_service.auth_settings.AUTO_LOGIN:
            if not settings_service.auth_settings.SUPERUSER:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing first superuser credentials",
                )
            if not query_param and not header_param:
                result = await get_user_by_username(db, settings_service.auth_settings.SUPERUSER)
                if result:
                    logger.warning(AUTO_LOGIN_WARNING)
                    return result
            else:
                # At least one of query_param or header_param is truthy
                api_key = query_param or header_param
                if api_key is None:  # pragma: no cover - guaranteed by the if-condition above
                    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing API key")
                result = await check_key(db, api_key)

        elif not query_param and not header_param:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="An API key must be passed as query or header",
            )

        elif query_param:
            result = await check_key(db, query_param)

        else:
            # header_param must be truthy here (query_param is falsy, and we passed the not-both-None check)
            if header_param is None:  # pragma: no cover - guaranteed by the elif chain above
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or missing API key")
            result = await check_key(db, header_param)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or missing API key",
            )

        if isinstance(result, User):
            return result

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid authentication result",
        )