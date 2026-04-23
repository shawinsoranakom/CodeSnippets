def query_attributes(self) -> dict[str, Any]:
        """Return state query attributes."""
        domain = self.state.domain
        response: dict[str, Any] = {}

        # When it's an assumed state, we will return empty state
        # This shouldn't happen because we set `commandOnlyOpenClose`
        # but Google still queries. Erroring here will cause device
        # to show up offline.
        if self.state.attributes.get(ATTR_ASSUMED_STATE):
            return response

        if domain in COVER_VALVE_DOMAINS:
            if self.state.state == STATE_UNKNOWN:
                raise SmartHomeError(
                    ERR_NOT_SUPPORTED, "Querying state is not supported"
                )

            position = self.state.attributes.get(COVER_VALVE_CURRENT_POSITION[domain])

            if position is not None:
                response["openPercent"] = position
            elif self.state.state != COVER_VALVE_STATES[domain]["closed"]:
                response["openPercent"] = 100
            else:
                response["openPercent"] = 0

        elif domain == binary_sensor.DOMAIN:
            if self.state.state == STATE_ON:
                response["openPercent"] = 100
            else:
                response["openPercent"] = 0

        return response