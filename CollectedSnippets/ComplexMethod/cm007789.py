def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        mobj = re.search(
            r'inline(?P<type>Video|Audio|YouTube)Data\.push\((?P<json_data>[^)]+)\);',
            webpage)
        if mobj is None:
            expired = self._html_search_regex(r'(?s)class="expired-(?:video|audio)".+?<span>(.+?)</span>', webpage, 'expired', None)
            if expired:
                raise ExtractorError('%s said: %s' % (self.IE_NAME, expired), expected=True)
            raise ExtractorError('Unable to extract video urls')

        urls_info = self._parse_json(
            mobj.group('json_data'), video_id, transform_source=js_to_json)

        if not isinstance(urls_info, list):
            urls_info = [urls_info]

        if mobj.group('type') == 'YouTube':
            return self.playlist_result([
                self.url_result(url_info['url']) for url_info in urls_info])

        formats = [{
            'url': url_info['url'],
            'vcodec': url_info.get('codec') if mobj.group('type') == 'Video' else 'none',
            'width': int_or_none(url_info.get('width')),
            'height': int_or_none(url_info.get('height')),
            'tbr': int_or_none(url_info.get('bitrate')),
            'filesize': int_or_none(url_info.get('filesize')),
        } for url_info in urls_info]

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }