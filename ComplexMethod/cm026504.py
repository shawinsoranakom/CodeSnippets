def _update_media_attributes(
        self, player: Player, queue: PlayerQueue | None
    ) -> None:
        """Update media attributes for the active queue item."""
        self._attr_media_artist = None
        self._attr_media_album_artist = None
        self._attr_media_album_name = None
        self._attr_media_title = None
        self._attr_media_content_id = None
        self._attr_media_duration = None
        self._attr_media_position = None
        self._attr_media_position_updated_at = None

        if queue is None and player.current_media:
            # player has some external source active
            self._attr_media_content_id = player.current_media.uri
            self._attr_app_id = player.active_source
            self._attr_media_title = player.current_media.title
            self._attr_media_artist = player.current_media.artist
            self._attr_media_album_name = player.current_media.album
            self._attr_media_duration = player.current_media.duration
            # shuffle and repeat are not (yet) supported for external sources
            self._attr_shuffle = None
            self._attr_repeat = None
            self._attr_media_position = int(player.elapsed_time or 0)
            self._attr_media_position_updated_at = (
                utc_from_timestamp(player.elapsed_time_last_updated)
                if player.elapsed_time_last_updated
                else None
            )
            self._prev_time = player.elapsed_time or 0
            return

        if queue is None:
            # player has no MA queue active
            self._attr_source = player.active_source
            self._attr_app_id = player.active_source
            return

        # player has an MA queue active (either its own queue or some group queue)
        self._attr_app_id = DOMAIN
        self._attr_shuffle = queue.shuffle_enabled
        self._attr_repeat = REPEAT_MODE_MAPPING_TO_HA.get(queue.repeat_mode)
        if not (cur_item := queue.current_item):
            # queue is empty
            return

        self._attr_media_content_id = queue.current_item.uri
        self._attr_media_duration = queue.current_item.duration
        self._attr_media_position = int(queue.elapsed_time)
        self._attr_media_position_updated_at = utc_from_timestamp(
            queue.elapsed_time_last_updated
        )
        self._prev_time = queue.elapsed_time

        # handle stream title (radio station icy metadata)
        if (stream_details := cur_item.streamdetails) and stream_details.stream_title:
            self._attr_media_album_name = cur_item.name
            if " - " in stream_details.stream_title:
                stream_title_parts = stream_details.stream_title.split(" - ", 1)
                self._attr_media_title = stream_title_parts[1]
                self._attr_media_artist = stream_title_parts[0]
            else:
                self._attr_media_title = stream_details.stream_title
            return

        if not (media_item := cur_item.media_item):
            # queue is not playing a regular media item (edge case?!)
            self._attr_media_title = cur_item.name
            return

        # queue is playing regular media item
        self._attr_media_title = media_item.name
        # for tracks we can extract more info
        if media_item.media_type == MediaType.TRACK:
            if TYPE_CHECKING:
                assert isinstance(media_item, Track)
            self._attr_media_artist = media_item.artist_str
            if media_item.version:
                self._attr_media_title += f" ({media_item.version})"
            if media_item.album:
                self._attr_media_album_name = media_item.album.name
                self._attr_media_album_artist = getattr(
                    media_item.album, "artist_str", None
                )