def _update_ha_state_from_sdk_cache(
        self,
        *,
        write_state: bool = True,
        update_supported_features: bool = True,
    ) -> None:
        """Update HA state from SDK's cache/HTTP poll attributes.

        This is the main method for updating this entity's HA attributes.
        Crucially, it also handles propagating metadata to followers if this is a leader.
        """
        LOGGER.debug(
            "Device %s: Updating HA state from SDK cache/HTTP poll",
            self.name or self.unique_id,
        )
        self._attr_available = self._device.available

        if not self._attr_available:
            self._attr_state = None
            self._clear_media_metadata()
            self._attr_source = None
            self._transport_capabilities = None
            if write_state:
                self.async_write_ha_state()
            return

        # Update common attributes first
        self._attr_volume_level = self._device.volume / 100
        self._attr_is_volume_muted = self._device.is_muted
        self._attr_source_list = list(self._device.supported_input_modes) or None

        # Determine current group role (leader/follower/standalone)
        group_snapshot = self._get_group_snapshot()

        metadata_device = self._metadata_device
        if group_snapshot.role == WiimGroupRole.FOLLOWER:
            LOGGER.debug(
                "Follower %s: Actively pulling metadata from leader %s",
                self.entity_id,
                metadata_device.udn,
            )

        if metadata_device.playing_status is not None:
            self._attr_state = SDK_TO_HA_STATE.get(
                metadata_device.playing_status, MediaPlayerState.IDLE
            )

        if metadata_device.play_mode is not None:
            self._attr_source = metadata_device.play_mode

        loop_state = metadata_device.loop_state
        self._attr_repeat = RepeatMode(loop_state.repeat)
        self._attr_shuffle = loop_state.shuffle

        if media := metadata_device.current_media:
            self._attr_media_title = media.title
            self._attr_media_artist = media.artist
            self._attr_media_album_name = media.album
            self._attr_media_image_url = media.image_url
            self._attr_media_content_id = media.uri
            self._attr_media_content_type = MediaType.MUSIC
            self._attr_media_duration = media.duration
            if self._attr_media_position != media.position:
                self._attr_media_position = media.position
                self._attr_media_position_updated_at = utcnow()
        else:
            self._clear_media_metadata()

        group_members = [
            entity_id
            for udn in group_snapshot.member_udns
            if (entity_id := self._get_entity_id_for_udn(udn)) is not None
        ]
        self._attr_group_members = group_members or ([self.entity_id])

        if update_supported_features:
            self._async_schedule_update_supported_features()

        if write_state:
            self.async_write_ha_state()