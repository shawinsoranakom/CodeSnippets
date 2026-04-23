async def async_step_exclude(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose entities to exclude from the domain on the bridge."""
        hk_options = self.hk_options
        domains = hk_options[CONF_DOMAINS]

        if user_input is not None:
            self.included_cameras = []
            entities = cv.ensure_list(user_input[CONF_ENTITIES])
            if CAMERA_DOMAIN in domains:
                camera_entities = _async_get_matching_entities(
                    self.hass, [CAMERA_DOMAIN]
                )
                self.included_cameras = [
                    entity_id
                    for entity_id in camera_entities
                    if entity_id not in entities
                ]
            hk_options[CONF_FILTER] = _make_entity_filter(
                include_domains=domains, exclude_entities=entities
            )
            if self.included_cameras:
                return await self.async_step_cameras()
            return await self.async_step_advanced()

        entity_filter = self.hk_options.get(CONF_FILTER, {})
        entities = entity_filter.get(CONF_INCLUDE_ENTITIES, [])

        all_supported_entities = _async_get_matching_entities(self.hass, domains)
        if not entities:
            entities = entity_filter.get(CONF_EXCLUDE_ENTITIES, [])

        # Strip out entities that no longer exist to prevent error in the UI
        default_value = [
            entity_id for entity_id in entities if entity_id in all_supported_entities
        ]

        return self.async_show_form(
            step_id="exclude",
            description_placeholders={
                "domains": await _async_domain_names(self.hass, domains)
            },
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ENTITIES, default=default_value
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            multiple=True,
                            include_entities=all_supported_entities,
                        )
                    ),
                }
            ),
        )