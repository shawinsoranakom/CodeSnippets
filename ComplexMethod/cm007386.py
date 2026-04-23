def _real_extract(self, url):
        video_id = self._match_id(url)

        data = self._download_json(
            'https://archive.vine.co/posts/%s.json' % video_id, video_id)

        def video_url(kind):
            for url_suffix in ('Url', 'URL'):
                format_url = data.get('video%s%s' % (kind, url_suffix))
                if format_url:
                    return format_url

        formats = []
        for quality, format_id in enumerate(('low', '', 'dash')):
            format_url = video_url(format_id.capitalize())
            if not format_url:
                continue
            # DASH link returns plain mp4
            if format_id == 'dash' and determine_ext(format_url) == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    format_url, video_id, mpd_id='dash', fatal=False))
            else:
                formats.append({
                    'url': format_url,
                    'format_id': format_id or 'standard',
                    'quality': quality,
                })
        self._sort_formats(formats)

        username = data.get('username')

        alt_title = 'Vine by %s' % username if username else None

        return {
            'id': video_id,
            'title': data.get('description') or alt_title or 'Vine video',
            'alt_title': alt_title,
            'thumbnail': data.get('thumbnailUrl'),
            'timestamp': unified_timestamp(data.get('created')),
            'uploader': username,
            'uploader_id': data.get('userIdStr'),
            'view_count': int_or_none(data.get('loops')),
            'like_count': int_or_none(data.get('likes')),
            'comment_count': int_or_none(data.get('comments')),
            'repost_count': int_or_none(data.get('reposts')),
            'formats': formats,
        }