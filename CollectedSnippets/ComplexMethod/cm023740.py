def to_native(self, validate_entity_id: bool = True) -> State | None:
        """Convert to an HA state object."""
        context = Context(
            id=self.context_id,
            user_id=self.context_user_id,
            parent_id=self.context_parent_id,
        )
        try:
            attrs = json_loads(self.attributes) if self.attributes else {}
        except JSON_DECODE_EXCEPTIONS:
            # When json_loads fails
            _LOGGER.exception("Error converting row to state: %s", self)
            return None
        if self.last_changed_ts is None or self.last_changed_ts == self.last_updated_ts:
            last_changed = last_updated = dt_util.utc_from_timestamp(
                self.last_updated_ts or 0
            )
        else:
            last_updated = dt_util.utc_from_timestamp(self.last_updated_ts or 0)
            last_changed = dt_util.utc_from_timestamp(self.last_changed_ts or 0)
        return State(
            self.entity_id or "",
            self.state,  # type: ignore[arg-type]
            # Join the state_attributes table on attributes_id to get the attributes
            # for newer states
            attrs,
            last_changed,
            last_updated,
            context=context,
            validate_entity_id=validate_entity_id,
        )