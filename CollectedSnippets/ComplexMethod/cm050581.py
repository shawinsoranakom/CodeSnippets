def _on_change_url(self):
        """ Keeping a 'onchange' because we want this behavior for the frontend.
        Changing the document / video external URL will populate some metadata on the form view.
        We only populate the field that are empty to avoid overriding user assigned values.
        The slide metadata are also fetched in create / write overrides to ensure consistency. """

        self.ensure_one()
        if self.url or self.document_google_url or self.image_google_url or self.video_url:
            slide_metadata, _error = self._fetch_external_metadata()
            if slide_metadata:
                self.update({
                    key: value
                    for key, value in slide_metadata.items()
                    if not self[key]
                })