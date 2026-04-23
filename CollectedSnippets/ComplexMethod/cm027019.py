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