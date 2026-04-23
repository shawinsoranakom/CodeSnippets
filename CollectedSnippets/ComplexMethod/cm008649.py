def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_real_webpage(url, video_id)
        stream_meta = self._parse_vue_element_attr('stream-page', webpage, video_id)

        player_page = self._download_webpage(
            stream_meta['stream-access']['video_source'], video_id,
            'Downloading player page', headers={'referer': 'https://zaiko.io/'})
        player_meta = self._parse_vue_element_attr('player', player_page, video_id)
        initial_event_info = traverse_obj(player_meta, ('initial_event_info', {dict})) or {}

        status = traverse_obj(initial_event_info, ('status', {str}))
        live_status, msg, expected = {
            'vod': ('was_live', 'No VOD stream URL was found', False),
            'archiving': ('post_live', 'Event VOD is still being processed', True),
            'deleting': ('post_live', 'This event has ended', True),
            'deleted': ('post_live', 'This event has ended', True),
            'error': ('post_live', 'This event has ended', True),
            'disconnected': ('post_live', 'Stream has been disconnected', True),
            'live_to_disconnected': ('post_live', 'Stream has been disconnected', True),
            'live': ('is_live', 'No livestream URL found was found', False),
            'waiting': ('is_upcoming', 'Live event has not yet started', True),
            'cancelled': ('not_live', 'Event has been cancelled', True),
        }.get(status) or ('not_live', f'Unknown event status "{status}"', False)

        if traverse_obj(initial_event_info, ('is_jwt_protected', {bool})):
            stream_url = self._download_json(
                initial_event_info['jwt_token_url'], video_id, 'Downloading JWT-protected stream URL',
                'Failed to download JWT-protected stream URL')['playback_url']
        else:
            stream_url = traverse_obj(initial_event_info, ('endpoint', {url_or_none}))

        formats = self._extract_m3u8_formats(
            stream_url, video_id, live=True, fatal=False) if stream_url else []
        if not formats:
            self.raise_no_formats(msg, expected=expected)

        thumbnail_urls = [
            traverse_obj(initial_event_info, ('poster_url', {url_or_none})),
            self._og_search_thumbnail(self._download_webpage(
                f'https://zaiko.io/event/{video_id}', video_id, 'Downloading event page', fatal=False) or ''),
        ]

        return {
            'id': video_id,
            'formats': formats,
            'live_status': live_status,
            **traverse_obj(stream_meta, {
                'title': ('event', 'name', {str}),
                'uploader': ('profile', 'name', {str}),
                'uploader_id': ('profile', 'id', {str_or_none}),
                'release_timestamp': ('stream', 'start', 'timestamp', {int_or_none}),
                'categories': ('event', 'genres', ..., filter),
            }),
            'alt_title': traverse_obj(initial_event_info, ('title', {str})),
            'thumbnails': [{'url': url, 'id': url_basename(url)} for url in thumbnail_urls if url_or_none(url)],
        }