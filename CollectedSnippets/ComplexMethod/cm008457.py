def _real_extract(self, url):
        channel_id = self._match_id(url)
        channel_data = self._download_json(
            'https://www.dr.dk/mu-online/api/1.0/channel/' + channel_id,
            channel_id)
        title = channel_data['Title']

        formats = []
        for streaming_server in channel_data.get('StreamingServers', []):
            server = streaming_server.get('Server')
            if not server:
                continue
            link_type = streaming_server.get('LinkType')
            for quality in streaming_server.get('Qualities', []):
                for stream in quality.get('Streams', []):
                    stream_path = stream.get('Stream')
                    if not stream_path:
                        continue
                    stream_url = update_url_query(
                        f'{server}/{stream_path}', {'b': ''})
                    if link_type == 'HLS':
                        formats.extend(self._extract_m3u8_formats(
                            stream_url, channel_id, 'mp4',
                            m3u8_id=link_type, fatal=False, live=True))
                    elif link_type == 'HDS':
                        formats.extend(self._extract_f4m_formats(update_url_query(
                            f'{server}/{stream_path}', {'hdcore': '3.7.0'}),
                            channel_id, f4m_id=link_type, fatal=False))

        return {
            'id': channel_id,
            'title': title,
            'thumbnail': channel_data.get('PrimaryImageUri'),
            'formats': formats,
            'is_live': True,
        }