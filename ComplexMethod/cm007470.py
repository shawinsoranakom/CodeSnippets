def _real_extract(self, url):
        video_id = self._match_id(url)

        data = self._download_json(
            'https://www.imdb.com/ve/data/VIDEO_PLAYBACK_DATA', video_id,
            query={
                'key': base64.b64encode(json.dumps({
                    'type': 'VIDEO_PLAYER',
                    'subType': 'FORCE_LEGACY',
                    'id': 'vi%s' % video_id,
                }).encode()).decode(),
            })[0]

        quality = qualities(('SD', '480p', '720p', '1080p'))
        formats = []
        for encoding in data['videoLegacyEncodings']:
            if not encoding or not isinstance(encoding, dict):
                continue
            video_url = url_or_none(encoding.get('url'))
            if not video_url:
                continue
            ext = mimetype2ext(encoding.get(
                'mimeType')) or determine_ext(video_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    preference=1, m3u8_id='hls', fatal=False))
                continue
            format_id = encoding.get('definition')
            formats.append({
                'format_id': format_id,
                'url': video_url,
                'ext': ext,
                'quality': quality(format_id),
            })
        self._sort_formats(formats)

        webpage = self._download_webpage(
            'https://www.imdb.com/video/vi' + video_id, video_id)
        video_metadata = self._parse_json(self._search_regex(
            r'args\.push\(\s*({.+?})\s*\)\s*;', webpage,
            'video metadata'), video_id)

        video_info = video_metadata.get('VIDEO_INFO')
        if video_info and isinstance(video_info, dict):
            info = try_get(
                video_info, lambda x: x[list(video_info.keys())[0]][0], dict)
        else:
            info = {}

        title = self._html_search_meta(
            ['og:title', 'twitter:title'], webpage) or self._html_search_regex(
            r'<title>(.+?)</title>', webpage, 'title',
            default=None) or info['videoTitle']

        return {
            'id': video_id,
            'title': title,
            'alt_title': info.get('videoSubTitle'),
            'formats': formats,
            'description': info.get('videoDescription'),
            'thumbnail': url_or_none(try_get(
                video_metadata, lambda x: x['videoSlate']['source'])),
            'duration': parse_duration(info.get('videoRuntime')),
        }