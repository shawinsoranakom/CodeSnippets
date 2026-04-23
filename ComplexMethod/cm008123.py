def _real_extract(self, url):
        lang, video_id = self._match_valid_url(url).group('lang', 'id')
        self._HEADERS['X-Target-Distribution'] = lang or 'fr'
        video_base_url = self._PLAYER_BASE_URL + f'video/{video_id}/'
        player = self._download_json(
            video_base_url + 'configuration', video_id,
            'Downloading player config JSON metadata',
            headers=self._HEADERS)['player']
        options = player['options']

        user = options['user']
        if not user.get('hasAccess'):
            start_date = traverse_obj(options, ('video', 'startDate', {str}))
            if (parse_iso8601(start_date) or 0) > time.time():
                raise ExtractorError(f'This video is not available yet. Release date: {start_date}', expected=True)
            self.raise_login_required('This video requires a subscription', method='password')

        token = self._download_json(
            user.get('refreshTokenUrl') or (self._PLAYER_BASE_URL + 'refresh/token'),
            video_id, 'Downloading access token', headers={
                'X-Player-Refresh-Token': user['refreshToken'],
            }, data=b'')['token']

        links_url = try_get(options, lambda x: x['video']['url']) or (video_base_url + 'link')
        self._K = ''.join(random.choices('0123456789abcdef', k=16))
        message = list(json.dumps({
            'k': self._K,
            't': token,
        }).encode())

        # Sometimes authentication fails for no good reason, retry with
        # a different random padding
        links_data = None
        for _ in range(3):
            padded_message = bytes(pkcs1pad(message, 128))
            n, e = self._RSA_KEY
            encrypted_message = long_to_bytes(pow(bytes_to_long(padded_message), e, n))
            authorization = base64.b64encode(encrypted_message).decode()

            try:
                links_data = self._download_json(
                    links_url, video_id, 'Downloading links JSON metadata', headers={
                        'X-Player-Token': authorization,
                        **self._HEADERS,
                    }, query={
                        'freeWithAds': 'true',
                        'adaptive': 'false',
                        'withMetadata': 'true',
                        'source': 'Web',
                    })
                break
            except ExtractorError as e:
                if not isinstance(e.cause, HTTPError):
                    raise e

                if e.cause.status == 401:
                    # This usually goes away with a different random pkcs1pad, so retry
                    continue

                error = self._parse_json(e.cause.response.read(), video_id)
                message = error.get('message')
                if e.cause.status == 403 and error.get('code') == 'player-bad-geolocation-country':
                    self.raise_geo_restricted(msg=message)
                raise ExtractorError(message)
        else:
            raise ExtractorError('Giving up retrying')

        links = links_data.get('links') or {}
        metas = links_data.get('metadata') or {}
        sub_url = (links.get('subtitles') or {}).get('all')
        video_info = links_data.get('video') or {}
        title = metas['title']

        formats = []
        for format_id, qualities in (links.get('streaming') or {}).items():
            if not isinstance(qualities, dict):
                continue
            for quality, load_balancer_url in qualities.items():
                load_balancer_data = self._download_json(
                    load_balancer_url, video_id,
                    f'Downloading {format_id} {quality} JSON metadata',
                    headers=self._HEADERS,
                    fatal=False) or {}
                m3u8_url = load_balancer_data.get('location')
                if not m3u8_url:
                    continue
                m3u8_formats = self._extract_m3u8_formats(
                    m3u8_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=format_id, fatal=False)
                if format_id == 'vf':
                    for f in m3u8_formats:
                        f['language'] = 'fr'
                elif format_id == 'vde':
                    for f in m3u8_formats:
                        f['language'] = 'de'
                formats.extend(m3u8_formats)

        if not formats:
            self.raise_login_required('This video requires a subscription', method='password')

        video = (self._download_json(
            self._API_BASE_URL + f'video/{video_id}', video_id,
            'Downloading additional video metadata', fatal=False, headers=self._HEADERS) or {}).get('video') or {}
        show = video.get('show') or {}

        return {
            'id': video_id,
            'title': title,
            'description': strip_or_none(metas.get('summary') or video.get('summary')),
            'thumbnail': video_info.get('image') or player.get('image'),
            'formats': formats,
            'subtitles': self.extract_subtitles(sub_url, video_id),
            'episode': metas.get('subtitle') or video.get('name'),
            'episode_number': int_or_none(video.get('shortNumber')),
            'series': show.get('title'),
            'season_number': int_or_none(video.get('season')),
            'duration': int_or_none(video_info.get('duration') or video.get('duration')),
            'release_date': unified_strdate(video.get('releaseDate')),
            'average_rating': float_or_none(video.get('rating') or metas.get('rating')),
            'comment_count': int_or_none(video.get('commentsCount')),
        }