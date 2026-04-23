def __init__(
        self,
        required_feature: int,
        source_key: str,
        source_list_key: str,
        *args: Any,
        category: int = CATEGORY_TELEVISION,
        **kwargs: Any,
    ) -> None:
        """Initialize a InputSelect accessory object."""
        super().__init__(*args, category=category, **kwargs)
        state = self.hass.states.get(self.entity_id)
        assert state
        features = state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        self._reload_on_change_attrs.extend((source_list_key,))
        self._mapped_sources_list: list[str] = []
        self._mapped_sources: dict[str, str] = {}
        self.source_key = source_key
        self.source_list_key = source_list_key
        self.sources = []
        self.support_select_source = False
        if features & required_feature:
            sources = self._get_ordered_source_list_from_state(state)
            if len(sources) > MAXIMUM_SOURCES:
                _LOGGER.warning(
                    "%s: Reached maximum number of sources (%s)",
                    self.entity_id,
                    MAXIMUM_SOURCES,
                )
            self.sources = sources[:MAXIMUM_SOURCES]
            if self.sources:
                self.support_select_source = True

        self.chars_tv = [CHAR_REMOTE_KEY]
        serv_tv = self.serv_tv = self.add_preload_service(
            SERV_TELEVISION, self.chars_tv
        )
        self.char_remote_key = self.serv_tv.configure_char(
            CHAR_REMOTE_KEY, setter_callback=self.set_remote_key
        )
        self.set_primary_service(serv_tv)
        serv_tv.configure_char(CHAR_CONFIGURED_NAME, value=self.display_name)
        serv_tv.configure_char(CHAR_SLEEP_DISCOVER_MODE, value=True)
        self.char_active = serv_tv.configure_char(
            CHAR_ACTIVE, setter_callback=self.set_on_off
        )

        if not self.support_select_source:
            return

        self.char_input_source = serv_tv.configure_char(
            CHAR_ACTIVE_IDENTIFIER, setter_callback=self.set_input_source
        )
        for index, source in enumerate(self.sources):
            serv_input = self.add_preload_service(
                SERV_INPUT_SOURCE, [CHAR_IDENTIFIER, CHAR_NAME], unique_id=source
            )
            serv_tv.add_linked_service(serv_input)
            serv_input.configure_char(CHAR_CONFIGURED_NAME, value=source)
            serv_input.configure_char(CHAR_NAME, value=source)
            serv_input.configure_char(CHAR_IDENTIFIER, value=index)
            serv_input.configure_char(CHAR_IS_CONFIGURED, value=True)
            input_type = 3 if "hdmi" in source.lower() else 0
            serv_input.configure_char(CHAR_INPUT_SOURCE_TYPE, value=input_type)
            serv_input.configure_char(CHAR_CURRENT_VISIBILITY_STATE, value=False)
            _LOGGER.debug("%s: Added source %s", self.entity_id, source)