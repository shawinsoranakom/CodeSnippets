def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        site_id, video_id = mobj.group('site_id'), mobj.group('id')

        data = None
        if site_id != 'vrtvideo':
            # Old API endpoint, serves more formats but may fail for some videos
            data = self._download_json(
                'https://mediazone.vrt.be/api/v1/%s/assets/%s'
                % (site_id, video_id), video_id, 'Downloading asset JSON',
                'Unable to download asset JSON', fatal=False)

        # New API endpoint
        if not data:
            headers = self.geo_verification_headers()
            headers.update({'Content-Type': 'application/json'})
            token = self._download_json(
                '%s/tokens' % self._REST_API_BASE, video_id,
                'Downloading token', data=b'', headers=headers)['vrtPlayerToken']
            data = self._download_json(
                '%s/videos/%s' % (self._REST_API_BASE, video_id),
                video_id, 'Downloading video JSON', query={
                    'vrtPlayerToken': token,
                    'client': '%s@PROD' % site_id,
                }, expected_status=400)
            if not data.get('title'):
                code = data.get('code')
                if code == 'AUTHENTICATION_REQUIRED':
                    self.raise_login_required()
                elif code == 'INVALID_LOCATION':
                    self.raise_geo_restricted(countries=['BE'])
                raise ExtractorError(data.get('message') or code, expected=True)

        title = data['title']
        description = data.get('description')

        formats = []
        for target in data['targetUrls']:
            format_url, format_type = url_or_none(target.get('url')), str_or_none(target.get('type'))
            if not format_url or not format_type:
                continue
            format_type = format_type.upper()
            if format_type in self._HLS_ENTRY_PROTOCOLS_MAP:
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', self._HLS_ENTRY_PROTOCOLS_MAP[format_type],
                    m3u8_id=format_type, fatal=False))
            elif format_type == 'HDS':
                formats.extend(self._extract_f4m_formats(
                    format_url, video_id, f4m_id=format_type, fatal=False))
            elif format_type == 'MPEG_DASH':
                formats.extend(self._extract_mpd_formats(
                    format_url, video_id, mpd_id=format_type, fatal=False))
            elif format_type == 'HSS':
                formats.extend(self._extract_ism_formats(
                    format_url, video_id, ism_id='mss', fatal=False))
            else:
                formats.append({
                    'format_id': format_type,
                    'url': format_url,
                })
        self._sort_formats(formats)

        subtitles = {}
        subtitle_urls = data.get('subtitleUrls')
        if isinstance(subtitle_urls, list):
            for subtitle in subtitle_urls:
                subtitle_url = subtitle.get('url')
                if subtitle_url and subtitle.get('type') == 'CLOSED':
                    subtitles.setdefault('nl', []).append({'url': subtitle_url})

        return {
            'id': video_id,
            'display_id': video_id,
            'title': title,
            'description': description,
            'formats': formats,
            'duration': float_or_none(data.get('duration'), 1000),
            'thumbnail': data.get('posterImageUrl'),
            'subtitles': subtitles,
        }