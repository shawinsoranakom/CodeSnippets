def _real_extract(self, url):
        video_id = self._match_id(url)
        video_base_url = self._PLAYER_BASE_URL + 'video/%s/' % video_id
        player = self._download_json(
            video_base_url + 'configuration', video_id,
            'Downloading player config JSON metadata',
            headers=self._HEADERS)['player']
        options = player['options']

        user = options['user']
        if not user.get('hasAccess'):
            self.raise_login_required()

        token = self._download_json(
            user.get('refreshTokenUrl') or (self._PLAYER_BASE_URL + 'refresh/token'),
            video_id, 'Downloading access token', headers={
                'x-player-refresh-token': user['refreshToken']
            }, data=b'')['token']

        links_url = try_get(options, lambda x: x['video']['url']) or (video_base_url + 'link')
        self._K = ''.join([random.choice('0123456789abcdef') for _ in range(16)])
        message = bytes_to_intlist(json.dumps({
            'k': self._K,
            't': token,
        }))

        # Sometimes authentication fails for no good reason, retry with
        # a different random padding
        links_data = None
        for _ in range(3):
            padded_message = intlist_to_bytes(pkcs1pad(message, 128))
            n, e = self._RSA_KEY
            encrypted_message = long_to_bytes(pow(bytes_to_long(padded_message), e, n))
            authorization = base64.b64encode(encrypted_message).decode()

            try:
                links_data = self._download_json(
                    links_url, video_id, 'Downloading links JSON metadata', headers={
                        'X-Player-Token': authorization
                    }, query={
                        'freeWithAds': 'true',
                        'adaptive': 'false',
                        'withMetadata': 'true',
                        'source': 'Web'
                    })
                break
            except ExtractorError as e:
                if not isinstance(e.cause, compat_HTTPError):
                    raise e

                if e.cause.code == 401:
                    # This usually goes away with a different random pkcs1pad, so retry
                    continue

                error = self._parse_json(
                    self._webpage_read_content(e.cause, links_url, video_id),
                    video_id, fatal=False) or {}
                message = error.get('message')
                if e.cause.code == 403 and error.get('code') == 'player-bad-geolocation-country':
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
                    'Downloading %s %s JSON metadata' % (format_id, quality),
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
                formats.extend(m3u8_formats)
        self._sort_formats(formats)

        video = (self._download_json(
            self._API_BASE_URL + 'video/%s' % video_id, video_id,
            'Downloading additional video metadata', fatal=False) or {}).get('video') or {}
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