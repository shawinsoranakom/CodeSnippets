def shared_attrs_bytes_from_event(
        event: Event[EventStateChangedData],
        dialect: SupportedDialect | None,
    ) -> bytes:
        """Create shared_attrs from a state_changed event."""
        # None state means the state was removed from the state machine
        if (state := event.data["new_state"]) is None:
            return b"{}"
        if state_info := state.state_info:
            unrecorded_attributes = state_info["unrecorded_attributes"]
            exclude_attrs = {
                *ALL_DOMAIN_EXCLUDE_ATTRS,
                *unrecorded_attributes,
            }
            if MATCH_ALL in unrecorded_attributes:
                # Don't exclude device class, state class, unit of measurement
                # or friendly name when using the MATCH_ALL exclude constant
                exclude_attrs.update(state.attributes)
                exclude_attrs -= _MATCH_ALL_KEEP
        else:
            exclude_attrs = ALL_DOMAIN_EXCLUDE_ATTRS
        encoder = json_bytes_strip_null if dialect == PSQL_DIALECT else json_bytes
        bytes_result = encoder(
            {k: v for k, v in state.attributes.items() if k not in exclude_attrs}
        )
        if len(bytes_result) > MAX_STATE_ATTRS_BYTES:
            _LOGGER.warning(
                "State attributes for %s exceed maximum size of %s bytes. "
                "This can cause database performance issues; Attributes "
                "will not be stored",
                state.entity_id,
                MAX_STATE_ATTRS_BYTES,
            )
            return b"{}"
        return bytes_result