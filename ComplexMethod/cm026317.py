async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play media."""
        media_type = media_type.removeprefix(MEDIA_PLAYER_PREFIX)

        enqueue: MediaPlayerEnqueue = kwargs.get(
            ATTR_MEDIA_ENQUEUE, MediaPlayerEnqueue.REPLACE
        )

        kwargs = {}

        # Spotify can't handle URI's with query strings or anchors
        # Yet, they do generate those types of URI in their official clients.
        media_id = str(URL(media_id).with_query(None).with_fragment(None))

        if media_type in {MediaType.TRACK, MediaType.EPISODE, MediaType.MUSIC}:
            kwargs["uris"] = [media_id]
        elif media_type in PLAYABLE_MEDIA_TYPES:
            context_uri = media_id

            if media_type == MEDIA_TYPE_USER_SAVED_TRACKS:
                user_data = await self.coordinator.client.get_current_user()
                context_uri = f"spotify:user:{user_data.user_id}:collection"

            kwargs["context_uri"] = context_uri
        else:
            _LOGGER.error("Media type %s is not supported", media_type)
            return

        if not self.currently_playing and self.devices.data:
            kwargs["device_id"] = self.devices.data[0].device_id

        if enqueue == MediaPlayerEnqueue.ADD:
            if media_type not in {
                MediaType.TRACK,
                MediaType.EPISODE,
                MediaType.MUSIC,
            }:
                raise ValueError(
                    f"Media type {media_type} is not supported when enqueue is ADD"
                )
            await self.coordinator.client.add_to_queue(
                media_id, kwargs.get("device_id")
            )
            return

        await self.coordinator.client.start_playback(**kwargs)