def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://www.tvp.pl/sess/tvplayer.php?object_id=%s' % video_id, video_id)

        error = self._html_search_regex(
            r'(?s)<p[^>]+\bclass=["\']notAvailable__text["\'][^>]*>(.+?)</p>',
            webpage, 'error', default=None) or clean_html(
            get_element_by_attribute('class', 'msg error', webpage))
        if error:
            raise ExtractorError('%s said: %s' % (
                self.IE_NAME, clean_html(error)), expected=True)

        title = self._search_regex(
            r'name\s*:\s*([\'"])Title\1\s*,\s*value\s*:\s*\1(?P<title>.+?)\1',
            webpage, 'title', group='title')
        series_title = self._search_regex(
            r'name\s*:\s*([\'"])SeriesTitle\1\s*,\s*value\s*:\s*\1(?P<series>.+?)\1',
            webpage, 'series', group='series', default=None)
        if series_title:
            title = '%s, %s' % (series_title, title)

        thumbnail = self._search_regex(
            r"poster\s*:\s*'([^']+)'", webpage, 'thumbnail', default=None)

        video_url = self._search_regex(
            r'0:{src:([\'"])(?P<url>.*?)\1', webpage,
            'formats', group='url', default=None)
        if not video_url or 'material_niedostepny.mp4' in video_url:
            video_url = self._download_json(
                'http://www.tvp.pl/pub/stat/videofileinfo?video_id=%s' % video_id,
                video_id)['video_url']

        formats = []
        video_url_base = self._search_regex(
            r'(https?://.+?/video)(?:\.(?:ism|f4m|m3u8)|-\d+\.mp4)',
            video_url, 'video base url', default=None)
        if video_url_base:
            # TODO: <Group> found instead of <AdaptationSet> in MPD manifest.
            # It's not mentioned in MPEG-DASH standard. Figure that out.
            # formats.extend(self._extract_mpd_formats(
            #     video_url_base + '.ism/video.mpd',
            #     video_id, mpd_id='dash', fatal=False))
            formats.extend(self._extract_ism_formats(
                video_url_base + '.ism/Manifest',
                video_id, 'mss', fatal=False))
            formats.extend(self._extract_f4m_formats(
                video_url_base + '.ism/video.f4m',
                video_id, f4m_id='hds', fatal=False))
            m3u8_formats = self._extract_m3u8_formats(
                video_url_base + '.ism/video.m3u8', video_id,
                'mp4', 'm3u8_native', m3u8_id='hls', fatal=False)
            self._sort_formats(m3u8_formats)
            m3u8_formats = list(filter(
                lambda f: f.get('vcodec') != 'none', m3u8_formats))
            formats.extend(m3u8_formats)
            for i, m3u8_format in enumerate(m3u8_formats, 2):
                http_url = '%s-%d.mp4' % (video_url_base, i)
                if self._is_valid_url(http_url, video_id):
                    f = m3u8_format.copy()
                    f.update({
                        'url': http_url,
                        'format_id': f['format_id'].replace('hls', 'http'),
                        'protocol': 'http',
                    })
                    formats.append(f)
        else:
            formats = [{
                'format_id': 'direct',
                'url': video_url,
                'ext': determine_ext(video_url, 'mp4'),
            }]

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'formats': formats,
        }