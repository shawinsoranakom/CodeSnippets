def _real_extract(self, url):
        video_id = self._match_id(url)
        playlist_id = self._extract_playlist_id(url, 'playlistId')

        if self._yes_playlist(playlist_id, video_id):
            return self._extract_playlist(playlist_id)

        data = self._download_json(f'{self._API_BASE}/videos/{video_id}', video_id)
        thumbnails = [{
            'id': f'{quality}p',
            'url': f'{self._CDN_BASE}/video/{video_id}/{quality}.webp',
        } for quality in [48, 96, 144, 240, 512, 1080]]

        formats = []
        url_data = self._download_json(f'{self._API_BASE}/videos/{video_id}/url', video_id, data=b'')
        if master_url := traverse_obj(url_data, ('src', 'hls', 'masterPlaylist', {url_or_none})):
            formats = self._extract_m3u8_formats(master_url, video_id, 'mp4', m3u8_id='hls', fatal=False)

        for format_id, format_url in traverse_obj(url_data, (
                'src', ('mp4', 'hls'), 'levels', {dict.items}, lambda _, v: url_or_none(v[1]))):
            ext = determine_ext(format_url)
            is_hls = ext == 'm3u8'
            formats.append({
                'url': format_url,
                'ext': 'mp4' if is_hls else ext,
                'format_id': join_nonempty(is_hls and 'hls', format_id),
                'protocol': 'm3u8_native' if is_hls else 'https',
                'height': int_or_none(format_id),
            })
        self._remove_duplicate_formats(formats)

        return {
            'id': video_id,
            'title': data.get('title'),
            'description': data.get('desc'),
            'uploader': traverse_obj(data, ('channel', 'name')),
            'channel_id': data.get('channelId'),
            'channel_url': format_field(data, 'channelId', 'https://banbye.com/channel/%s'),
            'timestamp': unified_timestamp(data.get('publishedAt')),
            'duration': data.get('duration'),
            'tags': data.get('tags'),
            'formats': formats,
            'thumbnails': thumbnails,
            'like_count': data.get('likes'),
            'dislike_count': data.get('dislikes'),
            'view_count': data.get('views'),
            'comment_count': data.get('commentCount'),
        }