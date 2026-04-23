def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        thumbnail = None
        formats = []

        def extract_m3u8(manifest_url):
            formats.extend(self._extract_m3u8_formats(
                manifest_url, video_id, 'mp4',
                entry_protocol='m3u8_native', m3u8_id='m3u8'))

        def extract_original(original_url):
            formats.append({
                'url': original_url,
                'format_id': determine_ext(original_url, None),
                'preference': 1,
            })

        playlist = self._parse_json(
            self._search_regex(
                r'options\s*=\s*({.+?});', webpage, 'options', default='{}'),
            video_id).get('playlist', {})
        if playlist:
            master = playlist.get('master')
            if isinstance(master, compat_str) and determine_ext(master) == 'm3u8':
                extract_m3u8(compat_urlparse.urljoin(url, master))
            original = playlist.get('original')
            if isinstance(original, compat_str):
                extract_original(original)
            thumbnail = playlist.get('image')

        # Old rendition fallback
        if not formats:
            for video_url in re.findall(r'"file"\s*:\s*"([^"]+)', webpage):
                video_url = compat_urlparse.urljoin(url, video_url)
                if determine_ext(video_url) == 'm3u8':
                    extract_m3u8(video_url)
                else:
                    extract_original(video_url)

        self._sort_formats(formats)

        thumbnail = thumbnail or self._search_regex(
            r'"image"\s*:\s*"([^"]+)', webpage, 'thumbnail', default=None)

        return {
            'id': video_id,
            'title': video_id,
            'thumbnail': thumbnail,
            'formats': formats,
        }