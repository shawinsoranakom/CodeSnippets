def _fetch_external_metadata(self, image_url_only=False):
        self.ensure_one()

        slide_metadata = {}
        error = False
        if self.slide_category == 'video' and self.video_source_type == 'youtube':
            slide_metadata, error = self._fetch_youtube_metadata(image_url_only)
        elif self.slide_category == 'video' and self.video_source_type == 'google_drive':
            slide_metadata, error = self._fetch_google_drive_metadata(image_url_only)
        elif self.slide_category == 'video' and self.video_source_type == 'vimeo':
            slide_metadata, error = self._fetch_vimeo_metadata(image_url_only)
        elif self.slide_category in ['document', 'infographic'] and self.source_type == 'external':
            # external documents & google drive videos share the same method currently
            slide_metadata, error = self._fetch_google_drive_metadata(image_url_only)

        return slide_metadata, error