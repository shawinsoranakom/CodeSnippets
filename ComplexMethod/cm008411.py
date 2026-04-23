def _real_extract(self, url):
        channel_url = self._match_id(url)
        channel_list = self._get_channel_list(channel_url)

        channel = next((c for c in channel_list if c.get('url') == channel_url), None)

        if not channel:
            raise ExtractorError('Channel not found')

        station_list = self._download_json(self._STATIONS_API_URL, channel_url,
                                           note='Downloading stream url list',
                                           headers={
                                               'Accept': 'application/json',
                                               'Referer': url,
                                               'Origin': self._BASE_URL,
                                           })
        station = next((s for s in station_list
                        if s.get('Name') == (channel.get('streamName') or channel.get('name'))), None)
        if not station:
            raise ExtractorError('Station not found even though we extracted channel')

        formats = []
        for stream_url in station['Streams']:
            stream_url = self._proto_relative_url(stream_url)
            if stream_url.endswith('/playlist.m3u8'):
                formats.extend(self._extract_m3u8_formats(stream_url, channel_url, live=True))
            elif stream_url.endswith('/manifest.f4m'):
                formats.extend(self._extract_mpd_formats(stream_url, channel_url))
            elif stream_url.endswith('/Manifest'):
                formats.extend(self._extract_ism_formats(stream_url, channel_url))
            else:
                formats.append({
                    'url': stream_url,
                })

        return {
            'id': str(channel['id']),
            'formats': formats,
            'title': channel.get('name') or channel.get('streamName'),
            'display_id': channel_url,
            'thumbnail': f'{self._BASE_URL}/images/{channel_url}-color-logo.png',
            'is_live': True,
        }