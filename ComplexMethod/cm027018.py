async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Splunk from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    token = entry.data[CONF_TOKEN]
    use_ssl = entry.data[CONF_SSL]
    verify_ssl = entry.data[CONF_VERIFY_SSL]
    name = entry.data.get(CONF_NAME) or hass.config.location_name

    # Get the entity filter from hass.data (set by async_setup or empty if no YAML)
    entity_filter: EntityFilter = hass.data.get(DATA_FILTER, FILTER_SCHEMA({}))

    event_collector = hass_splunk(
        session=async_get_clientsession(hass),
        host=host,
        port=port,
        token=token,
        use_ssl=use_ssl,
        verify_ssl=verify_ssl,
    )

    # Validate connectivity and token
    try:
        # Check connectivity first
        connectivity_ok = await event_collector.check(
            connectivity=True, token=False, busy=False
        )
        # Then check token validity (only if connectivity passed)
        token_ok = connectivity_ok and await event_collector.check(
            connectivity=False, token=True, busy=False
        )
    except ClientConnectionError as err:
        _LOGGER.debug("Connection error during setup at %s:%s: %s", host, port, err)
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
            translation_placeholders={"host": host, "port": str(port)},
        ) from err
    except TimeoutError as err:
        _LOGGER.debug("Timeout during setup at %s:%s: %s", host, port, err)
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="timeout_connect",
            translation_placeholders={"host": host, "port": str(port)},
        ) from err
    except Exception as err:
        _LOGGER.exception("Unexpected setup error at %s:%s", host, port)
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="unexpected_connect_error",
        ) from err

    if not connectivity_ok:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="cannot_connect",
            translation_placeholders={"host": host, "port": str(port)},
        )
    if not token_ok:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN, translation_key="invalid_auth"
        )

    # Send startup event
    payload: dict[str, Any] = {
        "time": time.time(),
        "host": name,
        "event": {
            "domain": DOMAIN,
            "meta": "Splunk integration has started",
        },
    }

    await event_collector.queue(json.dumps(payload, cls=JSONEncoder), send=False)

    async def splunk_event_listener(event: Event[EventStateChangedData]) -> None:
        """Listen for new messages on the bus and sends them to Splunk."""
        state = event.data.get("new_state")
        if state is None or not entity_filter(state.entity_id):
            return

        _state: float | str
        try:
            _state = state_helper.state_as_number(state)
        except ValueError:
            _state = state.state

        payload: dict[str, Any] = {
            "time": event.time_fired.timestamp(),
            "host": name,
            "event": {
                "domain": state.domain,
                "entity_id": state.object_id,
                "attributes": dict(state.attributes),
                "value": _state,
            },
        }

        try:
            await event_collector.queue(json.dumps(payload, cls=JSONEncoder), send=True)
        except SplunkPayloadError as err:
            if err.status == HTTPStatus.UNAUTHORIZED:
                _LOGGER.error("Splunk token unauthorized: %s", err)
                # Trigger reauth flow
                entry.async_start_reauth(hass)
            else:
                _LOGGER.warning("Splunk payload error: %s", err)
        except ClientConnectionError as err:
            _LOGGER.debug("Connection error sending to Splunk: %s", err)
        except TimeoutError:
            _LOGGER.debug("Timeout sending to Splunk at %s:%s", host, port)
        except ClientResponseError as err:
            _LOGGER.warning("Splunk response error: %s", err.message)
        except Exception:
            _LOGGER.exception("Unexpected error sending event to Splunk")

    # Store the event listener cancellation callback
    entry.async_on_unload(
        hass.bus.async_listen(EVENT_STATE_CHANGED, splunk_event_listener)
    )

    return True