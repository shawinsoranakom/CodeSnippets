def sync_attributes(self) -> dict[str, Any]:
        """Return opening direction."""
        response = {}
        features = self.state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)

        if self.state.domain == binary_sensor.DOMAIN:
            response["queryOnlyOpenClose"] = True
            response["discreteOnlyOpenClose"] = True
        elif (
            self.state.domain == cover.DOMAIN
            and features & CoverEntityFeature.SET_POSITION == 0
        ):
            response["discreteOnlyOpenClose"] = True

            if (
                features & CoverEntityFeature.OPEN == 0
                and features & CoverEntityFeature.CLOSE == 0
            ):
                response["queryOnlyOpenClose"] = True
        elif (
            self.state.domain == valve.DOMAIN
            and features & ValveEntityFeature.SET_POSITION == 0
        ):
            response["discreteOnlyOpenClose"] = True

            if (
                features & ValveEntityFeature.OPEN == 0
                and features & ValveEntityFeature.CLOSE == 0
            ):
                response["queryOnlyOpenClose"] = True

        if self.state.attributes.get(ATTR_ASSUMED_STATE):
            response["commandOnlyOpenClose"] = True

        return response