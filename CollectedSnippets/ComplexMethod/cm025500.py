def media_content_type(self) -> MediaType | str | None:
        """Content type of current playing media."""
        media_type = self.device.media_type
        if media_type == "Episode":
            return MediaType.TVSHOW
        if media_type == "Movie":
            return MediaType.MOVIE
        if media_type == "Trailer":
            return MEDIA_TYPE_TRAILER
        if media_type == "Music":
            return MediaType.MUSIC
        if media_type == "Video":
            return MediaType.VIDEO
        if media_type == "Audio":
            return MediaType.MUSIC
        if media_type == "TvChannel":
            return MediaType.CHANNEL
        return None