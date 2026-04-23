def _parse_video_info(self, video_info, username, user_id, display_id=None):
        video_id = str(video_info['id'])
        display_id = display_id or video_info.get('video_uuid')

        if traverse_obj(video_info, (
                None, ('transcoded_url', 'video_url', 'stream_url', 'audio_url'),
                {lambda x: re.search(r'/copyright/', x)}), get_all=False):
            self.raise_no_formats('This video has been removed due to licensing restrictions', expected=True)

        def format_info(url):
            return {
                'url': url,
                'ext': determine_ext(url),
                'format_id': url_basename(url).split('.')[0],
            }

        formats = []

        if determine_ext(video_info.get('transcoded_url')) == 'm3u8':
            formats.extend(self._extract_m3u8_formats(
                video_info['transcoded_url'], video_id, 'mp4', m3u8_id='hls', fatal=False))

        for video in traverse_obj(video_info, ('video_set', lambda _, v: url_or_none(v['url']))):
            formats.append({
                **format_info(video['url']),
                **parse_resolution(video.get('resolution')),
                'vcodec': video.get('codec'),
                'vbr': int_or_none(video.get('bitrate'), 1000),
            })

        video_url = traverse_obj(video_info, 'video_url', 'stream_url', expected_type=url_or_none)
        if video_url:
            formats.append({
                **format_info(video_url),
                'vcodec': 'h264',
                **traverse_obj(video_info, {
                    'width': 'width',
                    'height': 'height',
                    'filesize': 'filesize',
                }, expected_type=int_or_none),
            })

        audio_url = url_or_none(video_info.get('audio_url'))
        if audio_url:
            formats.append(format_info(audio_url))

        comment_count = traverse_obj(video_info, ('comment_count', {int_or_none}))

        return {
            'id': video_id,
            'display_id': display_id,
            'uploader': username,
            'uploader_id': user_id or traverse_obj(video_info, ('user', 'user_id', {str_or_none})),
            'webpage_url': urljoin(f'https://triller.co/@{username}/video/', display_id),
            'uploader_url': f'https://triller.co/@{username}',
            'extractor_key': TrillerIE.ie_key(),
            'extractor': TrillerIE.IE_NAME,
            'formats': formats,
            'comment_count': comment_count,
            '__post_extractor': self.extract_comments(video_id, comment_count),
            **traverse_obj(video_info, {
                'title': ('description', {lambda x: x.replace('\r\n', ' ')}),
                'description': 'description',
                'creator': ((('user'), ('users', lambda _, v: str(v['user_id']) == user_id)), 'name'),
                'thumbnail': ('thumbnail_url', {url_or_none}),
                'timestamp': ('timestamp', {unified_timestamp}),
                'duration': ('duration', {int_or_none}),
                'view_count': ('play_count', {int_or_none}),
                'like_count': ('likes_count', {int_or_none}),
                'artist': 'song_artist',
                'track': 'song_title',
            }, get_all=False),
        }