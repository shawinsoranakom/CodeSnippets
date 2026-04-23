async def _async_entity_state_listener(event: Event[EventStateChangedData]) -> None:
        """Handle state changes."""
        nonlocal unsub_pending, checker
        data = event.data
        new_state = data["new_state"]
        if TYPE_CHECKING:
            assert new_state is not None  # verified in filter
        entity = async_get_google_entity_if_supported_cached(
            hass, google_config, new_state
        )
        if TYPE_CHECKING:
            assert entity is not None  # verified in filter

        # We only trigger notifications on changes in the state value, not attributes.
        # This is mainly designed for our event entity types
        # We need to synchronize notifications using a `SYNC` response,
        # together with other state changes.
        if (
            (old_state := data["old_state"])
            and old_state.state != new_state.state
            and (notifications := entity.notifications_serialize()) is not None
        ):
            event_id = uuid4().hex
            payload = {
                "devices": {"notifications": {entity.state.entity_id: notifications}}
            }
            _LOGGER.info(
                "Sending event notification for entity %s",
                entity.state.entity_id,
            )
            result = await google_config.async_sync_notification_all(event_id, payload)
            if result != 200:
                _LOGGER.error(
                    "Unable to send notification with result code: %s, check log for more"
                    " info",
                    result,
                )

        changed_entity = data["entity_id"]
        try:
            entity_data = entity.query_serialize()
        except SmartHomeError as err:
            _LOGGER.debug("Not reporting state for %s: %s", changed_entity, err.code)
            return

        assert checker is not None
        if not checker.async_is_significant_change(new_state, extra_arg=entity_data):
            return

        _LOGGER.debug("Scheduling report state for %s: %s", changed_entity, entity_data)

        # If a significant change is already scheduled and we have another significant one,
        # let's create a new batch of changes
        if changed_entity in pending[-1]:
            pending.append({})

        pending[-1][changed_entity] = entity_data

        if unsub_pending is None:
            unsub_pending = async_call_later(
                hass, REPORT_STATE_WINDOW, report_states_job
            )