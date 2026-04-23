def _process_numeric_state(
        self, entity_observation: Observation, multi: bool = False
    ) -> bool | None:
        """Return True if numeric condition is met, return False if not, return None otherwise."""
        entity_id = entity_observation.entity_id
        # if we are dealing with numeric_state observations entity_id cannot be None
        if TYPE_CHECKING:
            assert entity_id is not None

        entity = self.hass.states.get(entity_id)
        if entity is None:
            return None

        try:
            if condition.state(self.hass, entity, [STATE_UNKNOWN, STATE_UNAVAILABLE]):
                return None
            result = condition.async_numeric_state(
                self.hass,
                entity,
                entity_observation.below,
                entity_observation.above,
                None,
                entity_observation.to_dict(),
            )
            if result:
                return True
            if multi:
                state = float(entity.state)
                if (
                    entity_observation.below is not None
                    and state == entity_observation.below
                ):
                    return True
                return None
        except ConditionError:
            return None
        else:
            return False