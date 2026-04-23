def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)
        video_info = self._search_nextjs_data(webpage, video_id)['props']['pageProps']['data']

        # Three types of video_info JSON: info in root, freeTv stream/item, event replay
        if not video_info.get('formattedIdMedia'):
            if traverse_obj(video_info, ('event', 'key')) == video_id:
                video_info = video_info['event']
            else:
                video_info = traverse_obj(video_info, (
                    ('freeTv', ('streams', ...)), 'items',
                    lambda _, v: v['key'].partition('-')[0] == video_id, any)) or {}

        video_stream_id = video_info.get('formattedIdMedia')
        if not video_stream_id:
            raise ExtractorError(
                'Couldn\'t find video metadata, maybe this livestream is now offline', expected=True)

        live_status = 'was_live' if video_info.get('isVodEnabled') else 'is_live'
        release_timestamp = traverse_obj(video_info, ('airDate', {parse_iso8601}))

        if live_status == 'is_live' and release_timestamp and release_timestamp > time.time():
            formats = []
            live_status = 'is_upcoming'
            self.raise_no_formats('This livestream has not yet started', expected=True)
        else:
            m3u8_url = self._call_media_api(video_stream_id, 'medianetlive', video_id)['url']
            formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4', live=live_status == 'is_live')

        return {
            'id': video_id,
            'formats': formats,
            'live_status': live_status,
            'release_timestamp': release_timestamp,
            **traverse_obj(video_info, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'thumbnail': ('images', 'card', 'url'),
            }),
        }