async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play media on the Cambridge Audio device."""

        if media_type not in {
            CAMBRIDGE_MEDIA_TYPE_PRESET,
            CAMBRIDGE_MEDIA_TYPE_AIRABLE,
            CAMBRIDGE_MEDIA_TYPE_INTERNET_RADIO,
        }:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unsupported_media_type",
                translation_placeholders={"media_type": media_type},
            )

        if media_type == CAMBRIDGE_MEDIA_TYPE_PRESET:
            try:
                preset_id = int(media_id)
            except ValueError as ve:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="preset_non_integer",
                    translation_placeholders={"preset_id": media_id},
                ) from ve
            preset = None
            for _preset in self.client.preset_list.presets:
                if _preset.preset_id == preset_id:
                    preset = _preset
            if not preset:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="missing_preset",
                    translation_placeholders={"preset_id": media_id},
                )
            await self.client.recall_preset(preset.preset_id)

        if media_type == CAMBRIDGE_MEDIA_TYPE_AIRABLE:
            preset_id = int(media_id)
            await self.client.play_radio_airable("Radio", preset_id)

        if media_type == CAMBRIDGE_MEDIA_TYPE_INTERNET_RADIO:
            await self.client.play_radio_url("Radio", media_id)