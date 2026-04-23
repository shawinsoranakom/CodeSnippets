async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, str]:
    """Validate the user input allows us to connect."""

    api: ComelitCommonApi

    if not re.fullmatch(r"[0-9]{4,10}", data[CONF_PIN]):
        raise InvalidPin

    session = await async_client_session(hass)
    if data.get(CONF_TYPE, BRIDGE) == BRIDGE:
        api = ComeliteSerialBridgeApi(
            data[CONF_HOST], data[CONF_PORT], data[CONF_PIN], session
        )
    else:
        api = ComelitVedoApi(data[CONF_HOST], data[CONF_PORT], data[CONF_PIN], session)

    try:
        await api.login()
    except (aiocomelit_exceptions.CannotConnect, TimeoutError) as err:
        raise CannotConnect(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
            translation_placeholders={"error": repr(err)},
        ) from err
    except aiocomelit_exceptions.CannotAuthenticate as err:
        raise InvalidAuth(
            translation_domain=DOMAIN,
            translation_key="cannot_authenticate",
            translation_placeholders={"error": repr(err)},
        ) from err
    finally:
        await api.logout()

    # Validate VEDO PIN if provided and device type is BRIDGE
    if data.get(CONF_VEDO_PIN) and data.get(CONF_TYPE, BRIDGE) == BRIDGE:
        if not re.fullmatch(r"[0-9]{4,10}", data[CONF_VEDO_PIN]):
            raise InvalidVedoPin

        if TYPE_CHECKING:
            assert isinstance(api, ComeliteSerialBridgeApi)

        # Verify VEDO is enabled with the provided PIN
        if not await api.vedo_enabled(data[CONF_VEDO_PIN]):
            raise InvalidVedoAuth

    return {"title": data[CONF_HOST]}