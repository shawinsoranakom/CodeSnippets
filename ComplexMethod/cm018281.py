def call_action(self, service: str, action: str, **kwargs: Any) -> Any:
        """Simulate TR-064 call with service name normalization."""
        LOGGER.debug(
            "_call_action service: %s, action: %s, **kwargs: %s",
            service,
            action,
            {**kwargs},
        )
        if self._side_effect:
            raise self._side_effect

        normalized = service
        if service not in self._fc_data:
            # tolerate DeviceInfo1 <-> DeviceInfo:1 and similar
            if (
                (":" in service and (alt := service.replace(":", "")) in self._fc_data)
                or (alt := f"{service}1") in self._fc_data
                or (alt := f"{service}:1") in self._fc_data
                or (
                    service.endswith("1")
                    and ":" not in service
                    and (alt := f"{service[:-1]}:1") in self._fc_data
                )
            ):
                normalized = alt

        action_data = self._fc_data.get(normalized, {}).get(action, {})
        if kwargs:
            if (index := kwargs.get("NewIndex")) is None:
                index = next(iter(kwargs.values()))
            if isinstance(action_data, dict) and index in action_data:
                return action_data[index]

        return action_data