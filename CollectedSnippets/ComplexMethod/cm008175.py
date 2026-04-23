def _real_extract(self, url):
        channel_id = self._match_id(url)

        try:
            stream_data = self._download_json(
                f'https://api.ttinglive.com/api/channels/{channel_id}/stream',
                channel_id, query={'option': 'all'})
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 400:
                raise UserNotLive(video_id=channel_id)
            raise

        formats = []
        for stream in traverse_obj(stream_data, ('sources', ..., {dict})):
            if stream.get('format') == 'ivs' and url_or_none(stream.get('url')):
                formats.extend(self._extract_m3u8_formats(
                    stream['url'], channel_id, 'mp4', live=True, fatal=False, m3u8_id='ivs'))
            for format_type in ['hls', 'flv']:
                for data in traverse_obj(stream, (
                        'urlDetail', format_type, 'resolution', lambda _, v: url_or_none(v['url']))):
                    formats.append({
                        'format_id': join_nonempty(format_type, data.get('suffixName'), delim=''),
                        'url': data['url'],
                        'height': int_or_none(data.get('resolution')),
                        'ext': 'mp4' if format_type == 'hls' else 'flv',
                        'protocol': 'm3u8_native' if format_type == 'hls' else 'http',
                    })

        return {
            'id': channel_id,
            'formats': formats,
            'is_live': True,
            **traverse_obj(stream_data, {
                'title': ('stream', 'title', {str}),
                'timestamp': ('stream', 'createdAt', {parse_iso8601}),
                'thumbnail': ('thumbUrl', {url_or_none}),
                'channel': ('owner', 'name', {str}),
                'channel_id': ('owner', 'id', {str_or_none}),
            }),
        }