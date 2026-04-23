def _real_extract(self, url):
        video_id = self._match_id(url)
        asset = self._download_json('https://sumo.tv2.no/rest/assets/' + video_id, video_id,
                                    'Downloading metadata JSON')
        title = asset['title']
        is_live = asset.get('live') is True

        formats = []
        format_urls = []
        for protocol in self._PROTOCOLS:
            try:
                data = self._download_json(f'https://api.sumo.tv2.no/play/{video_id}?stream={protocol}',
                                           video_id, 'Downloading playabck JSON',
                                           headers={'content-type': 'application/json'},
                                           data=b'{"device":{"id":"1-1-1","name":"Nettleser (HTML)"}}')['playback']
            except ExtractorError as e:
                if isinstance(e.cause, HTTPError) and e.cause.status == 401:
                    error = self._parse_json(e.cause.response.read().decode(), video_id)['error']
                    error_code = error.get('code')
                    if error_code == 'ASSET_PLAYBACK_INVALID_GEO_LOCATION':
                        self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
                    elif error_code == 'SESSION_NOT_AUTHENTICATED':
                        self.raise_login_required()
                    raise ExtractorError(error['description'])
                raise
            items = data.get('streams', [])
            for item in items:
                video_url = item.get('url')
                if not video_url or video_url in format_urls:
                    continue
                format_id = '{}-{}'.format(protocol.lower(), item.get('type'))
                if not self._is_valid_url(video_url, video_id, format_id):
                    continue
                format_urls.append(video_url)
                ext = determine_ext(video_url)
                if ext == 'f4m':
                    formats.extend(self._extract_f4m_formats(
                        video_url, video_id, f4m_id=format_id, fatal=False))
                elif ext == 'm3u8':
                    if not data.get('drmProtected'):
                        formats.extend(self._extract_m3u8_formats(
                            video_url, video_id, 'mp4', live=is_live, m3u8_id=format_id, fatal=False))
                elif ext == 'mpd':
                    formats.extend(self._extract_mpd_formats(
                        video_url, video_id, format_id, fatal=False))
                elif ext == 'ism' or video_url.endswith('.ism/Manifest'):
                    pass
                else:
                    formats.append({
                        'url': video_url,
                        'format_id': format_id,
                    })
        if not formats and data.get('drmProtected'):
            self.report_drm(video_id)

        thumbnails = [{
            'id': thumb_type,
            'url': thumb_url,
        } for thumb_type, thumb_url in (asset.get('images') or {}).items()]

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': strip_or_none(asset.get('description')),
            'thumbnails': thumbnails,
            'timestamp': parse_iso8601(asset.get('live_broadcast_time') or asset.get('update_time')),
            'duration': float_or_none(asset.get('accurateDuration') or asset.get('duration')),
            'view_count': int_or_none(asset.get('views')),
            'categories': asset.get('tags', '').split(','),
            'formats': formats,
            'is_live': is_live,
        }