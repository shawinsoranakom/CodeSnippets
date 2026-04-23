async def _async_handle_play_media(
        self,
        media_id: list[str],
        artist: str | None = None,
        album: str | None = None,
        enqueue: MediaPlayerEnqueue | QueueOption | None = None,
        radio_mode: bool | None = None,
        media_type: str | None = None,
    ) -> None:
        """Send the play_media command to the media player."""
        media_uris: list[str] = []
        item: MediaItemType | ItemMapping | None = None
        # work out (all) uri(s) to play
        for media_id_str in media_id:
            # URL or URI string
            if "://" in media_id_str:
                media_uris.append(media_id_str)
                continue
            # try content id as library id
            if media_type and media_id_str.isnumeric():
                with suppress(MediaNotFoundError):
                    item = await self.mass.music.get_item(
                        MediaType(media_type), media_id_str, "library"
                    )
                    if isinstance(item, MediaItemType | ItemMapping) and item.uri:
                        media_uris.append(item.uri)
                    continue
            # try local accessible filename
            elif await asyncio.to_thread(os.path.isfile, media_id_str):
                media_uris.append(media_id_str)
                continue
            # last resort: search for media item by name/search
            if item := await self.mass.music.get_item_by_name(
                name=media_id_str,
                artist=artist,
                album=album,
                media_type=MediaType(media_type) if media_type else None,
            ):
                if TYPE_CHECKING:
                    assert item.uri is not None
                media_uris.append(item.uri)

        if not media_uris:
            raise HomeAssistantError(
                f"Could not resolve {media_id} to playable media item"
            )

        # determine active queue to send the play request to
        if TYPE_CHECKING:
            assert self.player.active_source is not None
        if queue := self.mass.player_queues.get(self.player.active_source):
            queue_id = queue.queue_id
        else:
            queue_id = self.player_id

        await self.mass.player_queues.play_media(
            queue_id,
            media=media_uris,
            option=self._convert_queueoption_to_media_player_enqueue(enqueue),
            radio_mode=radio_mode or False,
        )