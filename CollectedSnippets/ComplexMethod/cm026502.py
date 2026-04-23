async def async_on_update(self) -> None:
        """Handle player updates."""
        if not self.available:
            return
        player = self.player
        active_queue = self.active_queue
        # update generic attributes
        if player.powered and player.playback_state is not None:
            self._attr_state = MediaPlayerState(player.playback_state.value)
        else:
            self._attr_state = MediaPlayerState(STATE_OFF)
        # active source and source list (translate to HA source names)
        source_mappings: dict[str, str] = {}
        active_source_name: str | None = None
        for source in player.source_list:
            if source.id == player.active_source:
                active_source_name = source.name
            if source.passive:
                # ignore passive sources because HA does not differentiate between
                # active and passive sources
                continue
            source_mappings[source.name] = source.id
        self._attr_source_list = list(source_mappings.keys())
        self._source_list_mapping = source_mappings
        self._attr_source = active_source_name

        # translation_key, sound_mode.id
        sound_mode_mappings: dict[str, str] = {}
        active_sound_mode_translation_key: str | None = None
        for sound_mode in player.sound_mode_list:
            if sound_mode.passive:
                # ignore passive sound_mode because HA does not differentiate between
                # active and passive sound mode
                continue
            translation_key = sound_mode.translation_key
            if player.active_sound_mode == sound_mode.id:
                active_sound_mode_translation_key = translation_key
            sound_mode_mappings[translation_key] = sound_mode.id

        self._attr_sound_mode_list = list(sound_mode_mappings.keys())
        self._sound_mode_list_mapping = sound_mode_mappings
        self._attr_sound_mode = active_sound_mode_translation_key

        group_members: list[str] = []
        if player.group_members:
            group_members = player.group_members
        elif player.synced_to and (parent := self.mass.players.get(player.synced_to)):
            group_members = parent.group_members

        # translate MA group_members to HA group_members as entity id's
        entity_registry = er.async_get(self.hass)
        group_members_entity_ids: list[str] = [
            entity_id
            for child_id in group_members
            if (
                entity_id := entity_registry.async_get_entity_id(
                    self.platform.domain, DOMAIN, child_id
                )
            )
        ]

        self._attr_group_members = group_members_entity_ids
        if player.type == PlayerType.GROUP:
            volume: int | None = player.group_volume
        else:
            volume = player.volume_level
        self._attr_volume_level = volume / 100 if volume is not None else None
        self._attr_is_volume_muted = player.volume_muted
        self._update_media_attributes(player, active_queue)
        self._update_media_image_url(player, active_queue)