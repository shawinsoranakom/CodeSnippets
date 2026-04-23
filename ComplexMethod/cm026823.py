async def async_step_cameras(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose camera config."""
        hk_options = self.hk_options
        all_entity_config: dict[str, dict[str, Any]]

        if user_input is not None:
            all_entity_config = hk_options[CONF_ENTITY_CONFIG]
            for entity_id in self.included_cameras:
                entity_config = all_entity_config.setdefault(entity_id, {})

                if entity_id in user_input[CONF_CAMERA_COPY]:
                    entity_config[CONF_VIDEO_CODEC] = VIDEO_CODEC_COPY
                elif CONF_VIDEO_CODEC in entity_config:
                    del entity_config[CONF_VIDEO_CODEC]

                if entity_id in user_input[CONF_CAMERA_AUDIO]:
                    entity_config[CONF_SUPPORT_AUDIO] = True
                elif CONF_SUPPORT_AUDIO in entity_config:
                    del entity_config[CONF_SUPPORT_AUDIO]

                if not entity_config:
                    all_entity_config.pop(entity_id)

            return await self.async_step_advanced()

        cameras_with_audio = []
        cameras_with_copy = []
        all_entity_config = hk_options.setdefault(CONF_ENTITY_CONFIG, {})
        for entity in self.included_cameras:
            entity_config = all_entity_config.get(entity, {})
            if entity_config.get(CONF_VIDEO_CODEC) == VIDEO_CODEC_COPY:
                cameras_with_copy.append(entity)
            if entity_config.get(CONF_SUPPORT_AUDIO):
                cameras_with_audio.append(entity)

        data_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_CAMERA_COPY, default=cameras_with_copy
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        multiple=True,
                        include_entities=(self.included_cameras),
                    )
                ),
                vol.Optional(
                    CONF_CAMERA_AUDIO, default=cameras_with_audio
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        multiple=True,
                        include_entities=(self.included_cameras),
                    )
                ),
            }
        )
        return self.async_show_form(step_id="cameras", data_schema=data_schema)