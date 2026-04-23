def __init__(
        self,
        hass: HomeAssistant,
        config: ConfigType,
    ) -> None:
        """Initialize the entity."""

        self.hass = hass
        self._config = config
        self._templates: dict[str, EntityTemplate] = {}
        self._action_scripts: dict[str, Script] = {}

        if self._optimistic_entity:
            optimistic = config.get(CONF_OPTIMISTIC)

            if self._state_option is not None:
                assumed_optimistic = config.get(self._state_option) is None
                if self._extra_optimistic_options:
                    assumed_optimistic = assumed_optimistic and all(
                        config.get(option) is None
                        for option in self._extra_optimistic_options
                    )

                self._attr_assumed_state = optimistic or (
                    optimistic is None and assumed_optimistic
                )

        if (default_entity_id := config.get(CONF_DEFAULT_ENTITY_ID)) is not None:
            _, _, object_id = default_entity_id.partition(".")
            self.entity_id = async_generate_entity_id(
                self._entity_id_format, object_id, hass=self.hass
            )

        device_registry = dr.async_get(hass)
        if (device_id := config.get(CONF_DEVICE_ID)) is not None:
            self.device_entry = device_registry.async_get(device_id)