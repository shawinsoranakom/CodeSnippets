async def _connect(
        self, user_input: dict[str, Any], errors: dict[str, str]
    ) -> Connection | None:
        """Try connecting with given data."""
        username = user_input.get(CONF_USERNAME) or ""
        password = user_input.get(CONF_PASSWORD) or ""

        def _get_connection() -> Connection:
            if (
                user_input[CONF_URL].startswith("https://")
                and not user_input[CONF_VERIFY_SSL]
            ):
                requests_session = non_verifying_requests_session(user_input[CONF_URL])
            else:
                requests_session = None

            return Connection(
                url=user_input[CONF_URL],
                username=username,
                password=password,
                timeout=CONNECTION_TIMEOUT,
                requests_session=requests_session,
            )

        conn = None
        try:
            conn = await self.hass.async_add_executor_job(_get_connection)
        except LoginErrorUsernameWrongException:
            errors[CONF_USERNAME] = "incorrect_username"
        except LoginErrorPasswordWrongException:
            errors[CONF_PASSWORD] = "incorrect_password"
        except LoginErrorUsernamePasswordWrongException:
            errors[CONF_USERNAME] = "invalid_auth"
        except LoginErrorUsernamePasswordOverrunException:
            errors["base"] = "login_attempts_exceeded"
        except ResponseErrorException:
            _LOGGER.warning("Response error", exc_info=True)
            errors["base"] = "response_error"
        except SSLError:
            _LOGGER.warning("SSL error", exc_info=True)
            if user_input[CONF_VERIFY_SSL]:
                errors[CONF_URL] = "ssl_error_try_unverified"
            else:
                errors[CONF_URL] = "ssl_error_try_plain"
        except Timeout:
            _LOGGER.warning("Connection timeout", exc_info=True)
            errors[CONF_URL] = "connection_timeout"
        except Exception:
            _LOGGER.exception("Unknown error connecting to device")
            errors[CONF_URL] = "unknown"
        return conn