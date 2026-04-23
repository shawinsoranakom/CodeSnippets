def _real_extract(self, url):
        lecture_id = self._match_id(url)

        webpage = self._download_webpage(url, lecture_id)

        data = self._parse_json(
            self._search_regex(
                # client_data may contain "};" so that we have to try more
                # strict regex first
                (r'client_data\s*=\s*({.+?})\s*;\s*\n',
                 r'client_data\s*=\s*({.+?})\s*;'),
                webpage, 'client data'),
            lecture_id)

        material = data['initialState']['material']
        desc = material['description']
        title = desc['title']

        formats = []
        for server_id, server in material['videos'].items():
            if not isinstance(server, dict):
                continue
            for format_id in ('hls', 'dash'):
                format_url = url_or_none(server.get(format_id))
                if not format_url:
                    continue
                if format_id == 'hls':
                    formats.extend(self._extract_m3u8_formats(
                        format_url, lecture_id, 'mp4',
                        entry_protocol='m3u8_native', m3u8_id=format_id,
                        note=f'Downloading {server_id} m3u8 information',
                        fatal=False))
                elif format_id == 'dash':
                    formats.extend(self._extract_mpd_formats(
                        format_url, lecture_id, mpd_id=format_id,
                        note=f'Downloading {server_id} MPD manifest',
                        fatal=False))

        content = str_or_none(desc.get('content'))
        description = (clean_html(base64.b64decode(content).decode('utf-8'))
                       if content else None)
        duration = int_or_none(material.get('duration'), invscale=60)

        return {
            'id': lecture_id,
            'title': title,
            'description': description,
            'duration': duration,
            'formats': formats,
        }