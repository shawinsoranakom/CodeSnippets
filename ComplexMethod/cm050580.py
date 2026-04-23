def _compute_google_drive_id(self):
        """ Extracts the Google Drive ID from the url based on the slide category. """

        for slide in self:
            url = slide.url or slide.document_google_url or slide.image_google_url or slide.video_url
            google_drive_id = False
            if url:
                match = re.match(self.GOOGLE_DRIVE_DOCUMENT_ID_REGEX, url)
                if match and len(match.groups()) == 2:
                    google_drive_id = match.group(2)

            slide.google_drive_id = google_drive_id