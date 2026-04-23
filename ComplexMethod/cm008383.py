def _extract_m3u8_formats_and_subtitles(
            self, m3u8_url, video_id, ext=None, entry_protocol='m3u8_native',
            preference=None, quality=None, m3u8_id=None, note=None,
            errnote=None, fatal=True, live=False, data=None, headers={},
            query={}):

        if self.get_param('ignore_no_formats_error'):
            fatal = False

        if not m3u8_url:
            if errnote is not False:
                errnote = errnote or 'Failed to obtain m3u8 URL'
                if fatal:
                    raise ExtractorError(errnote, video_id=video_id)
                self.report_warning(f'{errnote}{bug_reports_message()}')
            return [], {}
        if note is None:
            note = 'Downloading m3u8 information'
        if errnote is None:
            errnote = 'Failed to download m3u8 information'
        response = self._request_webpage(
            m3u8_url, video_id, note=note, errnote=errnote,
            fatal=fatal, data=data, headers=headers, query=query)
        if response is False:
            return [], {}

        with contextlib.closing(response):
            prefix = response.read(512)
            if not prefix.startswith(b'#EXTM3U'):
                msg = 'Response data has no m3u header'
                if fatal:
                    raise ExtractorError(msg, video_id=video_id)
                self.report_warning(f'{msg}{bug_reports_message()}', video_id=video_id)
                return [], {}

            content = self._webpage_read_content(
                response, m3u8_url, video_id, note=note, errnote=errnote,
                fatal=fatal, prefix=prefix, data=data)
        if content is False:
            return [], {}

        return self._parse_m3u8_formats_and_subtitles(
            content, response.url, ext=ext, entry_protocol=entry_protocol,
            preference=preference, quality=quality, m3u8_id=m3u8_id,
            note=note, errnote=errnote, fatal=fatal, live=live, data=data,
            headers=headers, query=query, video_id=video_id)