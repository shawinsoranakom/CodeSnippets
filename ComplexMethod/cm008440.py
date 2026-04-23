def _real_extract(self, url):
        space_id = self._match_id(url)
        space_data = self._call_graphql_api('HPEisOmj1epUNLCWTYhUWw/AudioSpaceById', space_id)['audioSpace']
        if not space_data:
            raise ExtractorError('Twitter Space not found', expected=True)

        metadata = space_data['metadata']
        live_status = try_call(lambda: self.SPACE_STATUS[metadata['state'].lower()])
        is_live = live_status == 'is_live'

        formats = []
        headers = {'Referer': 'https://twitter.com/'}
        if live_status == 'is_upcoming':
            self.raise_no_formats('Twitter Space not started yet', expected=True)
        elif not is_live and not metadata.get('is_space_available_for_replay'):
            self.raise_no_formats('Twitter Space ended and replay is disabled', expected=True)
        elif metadata.get('media_key'):
            source = traverse_obj(
                self._call_api(f'live_video_stream/status/{metadata["media_key"]}', metadata['media_key']),
                ('source', ('noRedirectPlaybackUrl', 'location'), {url_or_none}), get_all=False)
            is_audio_space = source and 'audio-space' in source
            formats = self._extract_m3u8_formats(
                source, metadata['media_key'], 'm4a' if is_audio_space else 'mp4',
                # XXX: Some audio-only Spaces need ffmpeg as downloader
                entry_protocol='m3u8' if is_audio_space else 'm3u8_native',
                live=is_live, headers=headers, fatal=False) if source else []
            if is_audio_space:
                for fmt in formats:
                    fmt.update({'vcodec': 'none', 'acodec': 'aac'})
                    if not is_live:
                        fmt['container'] = 'm4a_dash'

        participants = ', '.join(traverse_obj(
            space_data, ('participants', 'speakers', ..., 'display_name'))) or 'nobody yet'

        if not formats and live_status == 'post_live':
            self.raise_no_formats('Twitter Space ended but not downloadable yet', expected=True)

        return {
            'id': space_id,
            'description': f'Twitter Space participated by {participants}',
            'formats': formats,
            'http_headers': headers,
            'live_status': live_status,
            **traverse_obj(metadata, {
                'title': ('title', {str}),
                # started_at is None when stream is_upcoming so fallback to scheduled_start for --wait-for-video
                'release_timestamp': (('started_at', 'scheduled_start'), {int_or_none(scale=1000)}, any),
                'timestamp': ('created_at', {int_or_none(scale=1000)}),
            }),
            **traverse_obj(metadata, ('creator_results', 'result', 'legacy', {
                'uploader': ('name', {str}),
                'uploader_id': ('screen_name', {str_or_none}),
                'thumbnail': ('profile_image_url_https', {lambda x: x.replace('_normal', '_400x400')}, {url_or_none}),
            })),
        }