def _extract_video_info(self, video_data):
        video_id = compat_str(video_data['id'])

        FORMAT_KEYS = (
            ('sd', 'progressive_url'),
            ('hd', 'progressive_url_hd'),
        )

        formats = []
        for format_id, key in FORMAT_KEYS:
            video_url = video_data.get(key)
            if video_url:
                ext = determine_ext(video_url)
                if ext == 'm3u8':
                    continue
                bitrate = int_or_none(self._search_regex(
                    r'(\d+)\.%s' % ext, video_url, 'bitrate', default=None))
                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                    'tbr': bitrate,
                    'ext': ext,
                })

        smil_url = video_data.get('smil_url')
        if smil_url:
            formats.extend(self._extract_smil_formats(smil_url, video_id, fatal=False))

        m3u8_url = video_data.get('m3u8_url')
        if m3u8_url:
            formats.extend(self._extract_m3u8_formats(
                m3u8_url, video_id, 'mp4', 'm3u8_native',
                m3u8_id='hls', fatal=False))

        f4m_url = video_data.get('f4m_url')
        if f4m_url:
            formats.extend(self._extract_f4m_formats(
                f4m_url, video_id, f4m_id='hds', fatal=False))
        self._sort_formats(formats)

        comments = [{
            'author_id': comment.get('author_id'),
            'author': comment.get('author', {}).get('full_name'),
            'id': comment.get('id'),
            'text': comment['text'],
            'timestamp': parse_iso8601(comment.get('created_at')),
        } for comment in video_data.get('comments', {}).get('data', [])]

        return {
            'id': video_id,
            'formats': formats,
            'title': video_data['caption'],
            'description': video_data.get('description'),
            'thumbnail': video_data.get('thumbnail_url'),
            'duration': float_or_none(video_data.get('duration'), 1000),
            'timestamp': parse_iso8601(video_data.get('publish_at')),
            'like_count': video_data.get('likes', {}).get('total'),
            'comment_count': video_data.get('comments', {}).get('total'),
            'view_count': video_data.get('views'),
            'comments': comments,
        }