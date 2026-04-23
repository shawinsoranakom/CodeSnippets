def _real_extract(self, url):
        video_id = self._match_id(url)
        api_base = f'http://{self._API_DOMAIN}/api/web/asset/{video_id}'

        asset = self._download_json(
            api_base + '.json', video_id,
            'Downloading metadata JSON')['asset']
        title = asset.get('subtitle') or asset['title']
        is_live = asset.get('live') is True

        formats = []
        format_urls = []
        for protocol in self._PROTOCOLS:
            try:
                data = self._download_json(
                    api_base + f'/play.json?protocol={protocol}&videoFormat=SMIL+ISMUSP',
                    video_id, 'Downloading play JSON')['playback']
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
            items = try_get(data, lambda x: x['items']['item'])
            if not items:
                continue
            if not isinstance(items, list):
                items = [items]
            for item in items:
                if not isinstance(item, dict):
                    continue
                video_url = item.get('url')
                if not video_url or video_url in format_urls:
                    continue
                format_id = '{}-{}'.format(protocol.lower(), item.get('mediaFormat'))
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
                        'tbr': int_or_none(item.get('bitrate')),
                        'filesize': int_or_none(item.get('fileSize')),
                    })
        if not formats and data.get('drmProtected'):
            self.report_drm(video_id)

        thumbnails = [{
            'id': thumbnail.get('@type'),
            'url': thumbnail.get('url'),
        } for _, thumbnail in (asset.get('imageVersions') or {}).items()]

        return {
            'id': video_id,
            'url': video_url,
            'title': title,
            'description': strip_or_none(asset.get('description')),
            'thumbnails': thumbnails,
            'timestamp': parse_iso8601(asset.get('createTime')),
            'duration': float_or_none(asset.get('accurateDuration') or asset.get('duration')),
            'view_count': int_or_none(asset.get('views')),
            'categories': asset.get('keywords', '').split(','),
            'formats': formats,
            'is_live': is_live,
        }