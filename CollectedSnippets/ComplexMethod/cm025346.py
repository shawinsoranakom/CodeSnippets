async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on light."""
        params: dict[str, Any] = {"id": self._id, "on": True}

        if ATTR_BRIGHTNESS in kwargs:
            params["brightness"] = brightness_to_percentage(kwargs[ATTR_BRIGHTNESS])

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            params["ct"] = kwargs[ATTR_COLOR_TEMP_KELVIN]

        if ATTR_TRANSITION in kwargs:
            params["transition_duration"] = max(
                kwargs[ATTR_TRANSITION], RPC_MIN_TRANSITION_TIME_SEC
            )

        if ATTR_RGB_COLOR in kwargs:
            params["rgb"] = list(kwargs[ATTR_RGB_COLOR])

        if ATTR_RGBW_COLOR in kwargs:
            params["rgb"] = list(kwargs[ATTR_RGBW_COLOR][:-1])
            params["white"] = kwargs[ATTR_RGBW_COLOR][-1]

        if self.status.get("mode") is not None:
            if ATTR_COLOR_TEMP_KELVIN in kwargs:
                params["mode"] = "cct"
            elif ATTR_RGB_COLOR in kwargs:
                params["mode"] = "rgb"

        await self.call_rpc(f"{self._component}.Set", params)