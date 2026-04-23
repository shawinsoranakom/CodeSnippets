def _real_extract(self, url):
        webpage = self._download_webpage(
            url, 'temp_id', note='download video page')

        # There's no simple way to determine whether an URL is a playlist or not
        # Sometimes there are playlist links in individual videos, so treat it
        # as a single video first
        tvid = self._search_regex(
            r'data-(?:player|shareplattrigger)-tvid\s*=\s*[\'"](\d+)', webpage, 'tvid', default=None)
        if tvid is None:
            playlist_result = self._extract_playlist(webpage)
            if playlist_result:
                return playlist_result
            raise ExtractorError('Can\'t find any video')

        video_id = self._search_regex(
            r'data-(?:player|shareplattrigger)-videoid\s*=\s*[\'"]([a-f\d]+)', webpage, 'video_id')

        formats = []
        for _ in range(5):
            raw_data = self.get_raw_data(tvid, video_id)

            if raw_data['code'] != 'A00000':
                if raw_data['code'] == 'A00111':
                    self.raise_geo_restricted()
                raise ExtractorError('Unable to load data. Error code: ' + raw_data['code'])

            data = raw_data['data']

            for stream in data['vidl']:
                if 'm3utx' not in stream:
                    continue
                vd = compat_str(stream['vd'])
                formats.append({
                    'url': stream['m3utx'],
                    'format_id': vd,
                    'ext': 'mp4',
                    'preference': self._FORMATS_MAP.get(vd, -1),
                    'protocol': 'm3u8_native',
                })

            if formats:
                break

            self._sleep(5, video_id)

        self._sort_formats(formats)
        title = (get_element_by_id('widget-videotitle', webpage)
                 or clean_html(get_element_by_attribute('class', 'mod-play-tit', webpage))
                 or self._html_search_regex(r'<span[^>]+data-videochanged-title="word"[^>]*>([^<]+)</span>', webpage, 'title'))

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
        }