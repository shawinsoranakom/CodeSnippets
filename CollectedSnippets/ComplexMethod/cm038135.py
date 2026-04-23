def _extract_audio_from_videos(
        self,
        mm_items: MultiModalDataItems,
    ) -> tuple[MultiModalDataItems, list[AudioItem], list[bool]]:
        """Extract audio tracks from video bytes in *mm_items*.

        Videos whose bytes are missing or that contain no audio stream are
        silently skipped.  The returned *has_audio* mask is aligned with
        the video list so callers know which ``<video>`` tokens need an
        accompanying audio context.

        Returns:
            A 3-tuple of (augmented mm_items, extracted audio items,
            per-video boolean mask indicating which videos have audio).
        """
        videos = mm_items.get_items("video", VideoProcessorItems)
        assert isinstance(videos.metadata, list)

        metadata_list = videos.metadata

        audio_items: list[AudioItem] = []
        has_audio: list[bool] = []
        for idx, metadata in enumerate(metadata_list):
            video_bytes = metadata.get("original_video_bytes")
            if video_bytes is None or len(video_bytes) == 0:
                raise ValueError(
                    "Cannot extract audio from video: original_video_bytes is "
                    "missing or empty. When using use_audio_in_video=True, "
                    "video must be loaded with keep_video_bytes=True (e.g. via "
                    "the chat API with a model that sets use_audio_in_video)."
                )
            try:
                audio_items.append(load_audio_pyav(BytesIO(video_bytes)))
                has_audio.append(True)
            except Exception:
                logger.debug(
                    "Video %d: no audio stream found, skipping audio extraction.",
                    idx,
                    exc_info=True,
                )
                has_audio.append(False)

        # Create a new VideoProcessorItems with metadata that does not contain
        # the large video bytes, to avoid modifying the input `mm_items`.
        new_metadata_list = [
            {k: v for k, v in meta.items() if k != "original_video_bytes"}
            for meta in metadata_list
        ]
        new_videos = VideoProcessorItems(data=videos.data, metadata=new_metadata_list)

        audio_parsed = {}
        if audio_items:
            audio_parsed = self.data_parser.parse_mm_data({"audio": audio_items})

        # Create a new MultiModalDataItems with the new video and audio items.
        new_mm_items_dict = {**mm_items, **audio_parsed, "video": new_videos}
        mm_items = MultiModalDataItems(new_mm_items_dict)

        return mm_items, audio_items, has_audio