def _real_extract(self, url):
        domain, film_id = re.match(self._VALID_URL, url).groups()
        site = domain.split('.')[-2]
        if site in self._SITE_MAP:
            site = self._SITE_MAP[site]
        try:
            content_data = self._call_api(
                site, 'entitlement/video/status', film_id, {
                    'id': film_id
                })['video']
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                error_message = self._parse_json(e.cause.read().decode(), film_id).get('errorMessage')
                if error_message == 'User does not have a valid subscription or has not purchased this content.':
                    self.raise_login_required()
                raise ExtractorError(error_message, expected=True)
            raise
        gist = content_data['gist']
        title = gist['title']
        video_assets = content_data['streamingInfo']['videoAssets']

        formats = []
        mpeg_video_assets = video_assets.get('mpeg') or []
        for video_asset in mpeg_video_assets:
            video_asset_url = video_asset.get('url')
            if not video_asset:
                continue
            bitrate = int_or_none(video_asset.get('bitrate'))
            height = int_or_none(self._search_regex(
                r'^_?(\d+)[pP]$', video_asset.get('renditionValue'),
                'height', default=None))
            formats.append({
                'url': video_asset_url,
                'format_id': 'http%s' % ('-%d' % bitrate if bitrate else ''),
                'tbr': bitrate,
                'height': height,
                'vcodec': video_asset.get('codec'),
            })

        hls_url = video_assets.get('hls')
        if hls_url:
            formats.extend(self._extract_m3u8_formats(
                hls_url, film_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))
        self._sort_formats(formats, ('height', 'tbr', 'format_id'))

        info = {
            'id': film_id,
            'title': title,
            'description': gist.get('description'),
            'thumbnail': gist.get('videoImageUrl'),
            'duration': int_or_none(gist.get('runtime')),
            'age_limit': parse_age_limit(content_data.get('parentalRating')),
            'timestamp': int_or_none(gist.get('publishDate'), 1000),
            'formats': formats,
        }
        for k in ('categories', 'tags'):
            info[k] = [v['title'] for v in content_data.get(k, []) if v.get('title')]
        return info