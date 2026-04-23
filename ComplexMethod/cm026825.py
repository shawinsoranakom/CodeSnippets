async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle options flow."""
        if self.config_entry.source == SOURCE_IMPORT:
            return await self.async_step_yaml(user_input)

        if user_input is not None:
            self.hk_options.update(user_input)
            if self.hk_options.get(CONF_HOMEKIT_MODE) == HOMEKIT_MODE_ACCESSORY:
                return await self.async_step_accessory()
            if user_input[CONF_INCLUDE_EXCLUDE_MODE] == MODE_INCLUDE:
                return await self.async_step_include()
            return await self.async_step_exclude()

        self.hk_options = deepcopy(dict(self.config_entry.options))
        homekit_mode = self.hk_options.get(CONF_HOMEKIT_MODE, DEFAULT_HOMEKIT_MODE)
        entity_filter: EntityFilterDict = self.hk_options.get(CONF_FILTER, {})
        include_exclude_mode = MODE_INCLUDE
        entities = entity_filter.get(CONF_INCLUDE_ENTITIES, [])
        if homekit_mode != HOMEKIT_MODE_ACCESSORY:
            include_exclude_mode = MODE_INCLUDE if entities else MODE_EXCLUDE
        domains = entity_filter.get(CONF_INCLUDE_DOMAINS, [])
        if include_entities := entity_filter.get(CONF_INCLUDE_ENTITIES):
            domains.extend(_domains_set_from_entities(include_entities))
        name_to_type_map = await _async_name_to_type_map(self.hass)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOMEKIT_MODE, default=homekit_mode): vol.In(
                        HOMEKIT_MODES
                    ),
                    vol.Required(
                        CONF_INCLUDE_EXCLUDE_MODE, default=include_exclude_mode
                    ): vol.In(INCLUDE_EXCLUDE_MODES),
                    vol.Required(
                        CONF_DOMAINS,
                        default=domains,
                    ): cv.multi_select(name_to_type_map),
                }
            ),
        )