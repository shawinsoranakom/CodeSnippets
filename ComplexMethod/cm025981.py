async def _validate_auth(
    user_input: dict[str, str], entry: HeosConfigEntry, errors: dict[str, str]
) -> bool:
    """Validate authentication by signing in or out, otherwise populate errors if needed."""
    can_validate = (
        hasattr(entry, "runtime_data")
        and entry.runtime_data.heos.connection_state is ConnectionState.CONNECTED
    )
    if not user_input:
        # Log out (neither username nor password provided)
        if not can_validate:
            return True
        try:
            await entry.runtime_data.heos.sign_out()
        except HeosError:
            errors["base"] = "unknown"
            _LOGGER.exception("Unexpected error occurred during sign-out")
            return False
        else:
            _LOGGER.debug("Successfully signed-out of HEOS Account")
            return True

    # Ensure both username and password are provided
    authentication = CONF_USERNAME in user_input or CONF_PASSWORD in user_input
    if authentication and CONF_USERNAME not in user_input:
        errors[CONF_USERNAME] = "username_missing"
        return False
    if authentication and CONF_PASSWORD not in user_input:
        errors[CONF_PASSWORD] = "password_missing"
        return False

    # Attempt to login (both username and password provided)
    if not can_validate:
        return True
    try:
        await entry.runtime_data.heos.sign_in(
            user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
        )
    except CommandAuthenticationError as err:
        errors["base"] = "invalid_auth"
        _LOGGER.warning("Failed to sign-in to HEOS Account: %s", err)
        return False
    except HeosError:
        errors["base"] = "unknown"
        _LOGGER.exception("Unexpected error occurred during sign-in")
        return False
    else:
        _LOGGER.debug(
            "Successfully signed-in to HEOS Account: %s",
            entry.runtime_data.heos.signed_in_username,
        )
        return True