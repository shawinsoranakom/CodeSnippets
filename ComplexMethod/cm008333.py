def _download_media_selector(self, programme_id):
        last_exception = None
        formats, subtitles = [], {}
        for media_set in self._MEDIA_SETS:
            try:
                fmts, subs = self._download_media_selector_url(
                    self._MEDIA_SELECTOR_URL_TEMPL % (media_set, programme_id), programme_id)
                formats.extend(fmts)
                if subs:
                    self._merge_subtitles(subs, target=subtitles)
            except BBCCoUkIE.MediaSelectionError as e:
                if e.id in ('notukerror', 'geolocation', 'selectionunavailable'):
                    last_exception = e
                    continue
                self._raise_extractor_error(e)
        if last_exception:
            if formats or subtitles:
                self.report_warning(f'{self.IE_NAME} returned error: {last_exception.id}')
            else:
                self._raise_extractor_error(last_exception)
        return formats, subtitles