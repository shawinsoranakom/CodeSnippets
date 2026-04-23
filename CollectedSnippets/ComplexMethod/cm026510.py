async def validate_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> tuple[dict[str, str], str | None]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    Returns a tuple of (errors dict, device_id). If validation succeeds, errors will be empty.
    """
    api = KioskerAPI(
        host=data[CONF_HOST],
        port=PORT,
        token=data[CONF_API_TOKEN],
        ssl=data[CONF_SSL],
        verify=data[CONF_VERIFY_SSL],
    )

    try:
        # Test connection by getting status
        status = await hass.async_add_executor_job(api.status)
    except ConnectionError:
        return ({"base": "cannot_connect"}, None)
    except AuthenticationError:
        return ({"base": "invalid_auth"}, None)
    except IPAuthenticationError:
        return ({"base": "invalid_ip_auth"}, None)
    except TLSVerificationError:
        return ({"base": "tls_error"}, None)
    except BadRequestError:
        return ({"base": "bad_request"}, None)
    except PingError:
        return ({"base": "cannot_connect"}, None)
    except Exception:
        _LOGGER.exception("Unexpected exception while connecting to Kiosker")
        return ({"base": "unknown"}, None)

    # Ensure we have a device_id from the status response
    if not status.device_id:
        _LOGGER.error("Device did not return a valid device_id")
        return ({"base": "cannot_connect"}, None)

    return ({}, status.device_id)