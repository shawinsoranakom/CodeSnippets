def update_media_from_event(self, evars: dict[str, Any]) -> None:
        """Update information about currently playing media using an event payload."""
        new_status = evars["transport_state"]
        state_changed = new_status != self.playback_status

        self.play_mode = evars["current_play_mode"]
        self.playback_status = new_status

        track_uri = evars["enqueued_transport_uri"] or evars["current_track_uri"]
        audio_source = self.soco.music_source_from_uri(track_uri)

        self.set_basic_track_info(update_position=state_changed)

        if ct_md := evars["current_track_meta_data"]:
            if not self.image_url:
                if album_art_uri := getattr(ct_md, "album_art_uri", None):
                    self.image_url = self.library.build_album_art_full_uri(
                        album_art_uri
                    )

        et_uri_md = evars["enqueued_transport_uri_meta_data"]
        if isinstance(et_uri_md, DidlPlaylistContainer):
            self.playlist_name = et_uri_md.title

        if queue_size := evars.get("number_of_tracks", 0):
            self.queue_size = int(queue_size)

        if audio_source == MUSIC_SRC_RADIO:
            if et_uri_md:
                self.channel = et_uri_md.title

            # Extra guards for S1 compatibility
            if ct_md and hasattr(ct_md, "radio_show") and ct_md.radio_show:
                radio_show = ct_md.radio_show.split(",")[0]
                self.channel = " • ".join(filter(None, [self.channel, radio_show]))

            if isinstance(et_uri_md, DidlAudioBroadcast):
                self.title = self.title or self.channel

        self.write_media_player_states()