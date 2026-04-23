def _play_media(
        self, media_type: MediaType | str, media_id: str, is_radio: bool, **kwargs: Any
    ) -> None:
        """Wrap sync calls to async_play_media."""
        _LOGGER.debug("_play_media media_type %s media_id %s", media_type, media_id)
        enqueue = kwargs.get(ATTR_MEDIA_ENQUEUE, MediaPlayerEnqueue.REPLACE)

        if media_type == "favorite_item_id":
            favorite = self.speaker.favorites.lookup_by_item_id(media_id)
            if favorite is None:
                raise ValueError(f"Missing favorite for media_id: {media_id}")
            self._play_favorite(favorite)
            return

        soco = self.coordinator.soco
        if media_id and media_id.startswith(PLEX_URI_SCHEME):
            plex_plugin = self.speaker.plex_plugin
            result = process_plex_payload(
                self.hass, media_type, media_id, supports_playqueues=False
            )
            if result.shuffle:
                self.set_shuffle(True)
            if enqueue == MediaPlayerEnqueue.ADD:
                plex_plugin.add_to_queue(result.media, timeout=LONG_SERVICE_TIMEOUT)
            elif enqueue in (
                MediaPlayerEnqueue.NEXT,
                MediaPlayerEnqueue.PLAY,
            ):
                pos = (self.media.queue_position or 0) + 1
                new_pos = plex_plugin.add_to_queue(
                    result.media, position=pos, timeout=LONG_SERVICE_TIMEOUT
                )
                if enqueue == MediaPlayerEnqueue.PLAY:
                    soco.play_from_queue(new_pos - 1)
            elif enqueue == MediaPlayerEnqueue.REPLACE:
                soco.clear_queue()
                plex_plugin.add_to_queue(result.media, timeout=LONG_SERVICE_TIMEOUT)
                soco.play_from_queue(0)
            return

        share_link = self.coordinator.share_link
        if share_link.is_share_link(media_id):
            title = kwargs.get(ATTR_MEDIA_EXTRA, {}).get("title", "")
            self._play_media_sharelink(
                soco=soco,
                media_type=media_type,
                media_id=media_id,
                enqueue=enqueue,
                title=title,
            )
        elif media_type == MEDIA_TYPE_DIRECTORY:
            self._play_media_directory(
                soco=soco, media_type=media_type, media_id=media_id, enqueue=enqueue
            )
        elif media_type in {MediaType.MUSIC, MediaType.TRACK}:
            # If media ID is a relative URL, we serve it from HA.
            media_id = async_process_play_media_url(self.hass, media_id)

            if enqueue == MediaPlayerEnqueue.ADD:
                soco.add_uri_to_queue(media_id, timeout=LONG_SERVICE_TIMEOUT)
            elif enqueue in (
                MediaPlayerEnqueue.NEXT,
                MediaPlayerEnqueue.PLAY,
            ):
                pos = (self.media.queue_position or 0) + 1
                new_pos = soco.add_uri_to_queue(
                    media_id, position=pos, timeout=LONG_SERVICE_TIMEOUT
                )
                if enqueue == MediaPlayerEnqueue.PLAY:
                    soco.play_from_queue(new_pos - 1)
            elif enqueue == MediaPlayerEnqueue.REPLACE:
                soco.play_uri(media_id, force_radio=is_radio)
        elif media_type == MediaType.PLAYLIST:
            if media_id.startswith("S:"):
                playlist = media_browser.get_media(
                    self.media.library, media_id, media_type
                )
            else:
                playlists = soco.get_sonos_playlists(complete_result=True)
                playlist = next((p for p in playlists if p.title == media_id), None)
            if not playlist:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_sonos_playlist",
                    translation_placeholders={
                        "name": media_id,
                    },
                )
            soco.clear_queue()
            soco.add_to_queue(playlist, timeout=LONG_SERVICE_TIMEOUT)
            soco.play_from_queue(0)
        elif media_type in PLAYABLE_MEDIA_TYPES:
            item = media_browser.get_media(self.media.library, media_id, media_type)
            if not item:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_media",
                    translation_placeholders={
                        "media_id": media_id,
                    },
                )
            self._play_media_queue(soco, item, enqueue)
        else:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_content_type",
                translation_placeholders={
                    "media_type": media_type,
                },
            )