def update_media(self, media):
        """Update attributes from a media object."""
        self.media_content_id = media.ratingKey
        self.media_content_rating = getattr(media, "contentRating", None)
        self.media_image_url = self.get_media_image_url(media)
        self.media_summary = media.summary
        self.media_title = media.title

        if media.duration:
            self.media_duration = int(media.duration / 1000)

        if media.librarySectionID in SPECIAL_SECTIONS:
            self.media_library_title = SPECIAL_SECTIONS[media.librarySectionID]
        elif media.librarySectionID and media.librarySectionID < 1:
            self.media_library_title = UNKNOWN_SECTION
            _LOGGER.warning(
                (
                    "Unknown library section ID (%s) for title '%s',"
                    " please create an issue"
                ),
                media.librarySectionID,
                media.title,
            )
        else:
            self.media_library_title = (
                media.section().title if media.librarySectionID is not None else ""
            )

        if media.type == "episode":
            self.media_content_type = MediaType.TVSHOW
            self.media_season = media.seasonNumber
            self.media_series_title = media.grandparentTitle
            if media.index is not None:
                self.media_episode = media.index
            self.sensor_title = (
                f"{self.media_series_title} -"
                f" {media.seasonEpisode} -"
                f" {self.media_title}"
            )
        elif media.type == "movie":
            self.media_content_type = MediaType.MOVIE
            if media.year is not None and media.title is not None:
                self.media_title += f" ({media.year!s})"
            self.sensor_title = self.media_title
        elif media.type == "track":
            self.media_content_type = MediaType.MUSIC
            self.media_album_name = media.parentTitle
            self.media_album_artist = media.grandparentTitle
            self.media_track = media.index
            self.media_artist = media.originalTitle or self.media_album_artist
            self.sensor_title = (
                f"{self.media_artist} - {self.media_album_name} - {self.media_title}"
            )
        elif media.type == "clip":
            self.media_content_type = MediaType.VIDEO
            self.sensor_title = media.title
        else:
            self.sensor_title = "Unknown"