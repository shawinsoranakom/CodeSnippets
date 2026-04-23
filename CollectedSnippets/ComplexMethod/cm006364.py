async def ws_api_key_security(self, api_key: str | None) -> UserRead:
        settings = self.settings
        async with session_scope() as db:
            if settings.auth_settings.AUTO_LOGIN:
                if not settings.auth_settings.SUPERUSER:
                    raise WebSocketException(
                        code=status.WS_1011_INTERNAL_ERROR,
                        reason="Missing first superuser credentials",
                    )
                if not api_key:
                    if settings.auth_settings.skip_auth_auto_login:
                        result = await get_user_by_username(db, settings.auth_settings.SUPERUSER)
                        logger.warning(AUTO_LOGIN_WARNING)
                    else:
                        raise WebSocketException(
                            code=status.WS_1008_POLICY_VIOLATION,
                            reason=AUTO_LOGIN_ERROR,
                        )
                else:
                    result = await check_key(db, api_key)

            else:
                if not api_key:
                    raise WebSocketException(
                        code=status.WS_1008_POLICY_VIOLATION,
                        reason="An API key must be passed as query or header",
                    )
                result = await check_key(db, api_key)

            if not result:
                raise WebSocketException(
                    code=status.WS_1008_POLICY_VIOLATION,
                    reason="Invalid or missing API key",
                )

            if isinstance(result, User):
                return UserRead.model_validate(result, from_attributes=True)

        raise WebSocketException(
            code=status.WS_1011_INTERNAL_ERROR,
            reason="Authentication subsystem error",
        )