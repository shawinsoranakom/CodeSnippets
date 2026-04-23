def _extract_mpd_formats_and_subtitles(
            self, mpd_url, video_id, mpd_id=None, note=None, errnote=None,
            fatal=True, data=None, headers=None, query=None):

        # TODO: or not? param not yet implemented
        if self.get_param('ignore_no_formats_error'):
            fatal = False

        res = self._download_xml_handle(
            mpd_url, video_id,
            note='Downloading MPD manifest' if note is None else note,
            errnote='Failed to download MPD manifest' if errnote is None else errnote,
            fatal=fatal, data=data, headers=headers or {}, query=query or {})
        if res is False:
            return [], {}
        mpd_doc, urlh = res
        if mpd_doc is None:
            return [], {}

        # We could have been redirected to a new url when we retrieved our mpd file.
        mpd_url = urlh.geturl()
        mpd_base_url = base_url(mpd_url)

        return self._parse_mpd_formats_and_subtitles(
            mpd_doc, mpd_id, mpd_base_url, mpd_url)