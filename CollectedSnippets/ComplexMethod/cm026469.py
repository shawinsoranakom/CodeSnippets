async def validate_login(
    hass: HomeAssistant,
    data: dict[str, Any],
    email: str | None = None,
    password: str | None = None,
) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user. Upon success a session will be saved
    """

    if not email:
        email = data[CONF_EMAIL]
    if not password:
        password = data[CONF_PASSWORD]
    monarch_client = TypedMonarchMoney()
    if CONF_MFA_CODE in data:
        mfa_code = data[CONF_MFA_CODE]
        LOGGER.debug("Attempting to authenticate with MFA code")
        try:
            await monarch_client.multi_factor_authenticate(email, password, mfa_code)
        except KeyError as err:
            # A bug in the backing lib that I don't control throws a KeyError if the MFA code is wrong
            LOGGER.debug("Bad MFA Code")
            raise BadMFA from err
    else:
        LOGGER.debug("Attempting to authenticate")
        try:
            await monarch_client.login(
                email=email,
                password=password,
                save_session=False,
                use_saved_session=False,
            )
        except RequireMFAException:
            raise
        except LoginFailedException as err:
            raise InvalidAuth from err

    LOGGER.debug("Connection successful - saving session to file %s", SESSION_FILE)
    LOGGER.debug("Obtaining subscription id")
    subs: MonarchSubscription = await monarch_client.get_subscription_details()
    assert subs is not None
    subscription_id = subs.id
    return {
        CONF_TOKEN: monarch_client.token,
        CONF_ID: subscription_id,
    }