def _real_extract(self, url):
        locale, video_id = re.match(self._VALID_URL, url).groups()

        video = self._call_api('videos', 'id', video_id, locale, '''body
    locked
    rating
    thumbnail_url
    title''')[0]
        title = video['title'].strip()
        rating = video.get('rating')

        query = {}
        if video.get('locked'):
            resource = self._get_mvpd_resource(
                'VICELAND', title, video_id, rating)
            query['tvetoken'] = self._extract_mvpd_auth(
                url, video_id, 'VICELAND', resource)

        # signature generation algorithm is reverse engineered from signatureGenerator in
        # webpack:///../shared/~/vice-player/dist/js/vice-player.js in
        # https://www.viceland.com/assets/common/js/web.vendor.bundle.js
        # new JS is located here https://vice-web-statics-cdn.vice.com/vice-player/player-embed.js
        exp = int(time.time()) + 1440

        query.update({
            'exp': exp,
            'sign': hashlib.sha512(('%s:GET:%d' % (video_id, exp)).encode()).hexdigest(),
            'skipadstitching': 1,
            'platform': 'desktop',
            'rn': random.randint(10000, 100000),
        })

        try:
            preplay = self._download_json(
                'https://vms.vice.com/%s/video/preplay/%s' % (locale, video_id),
                video_id, query=query)
        except ExtractorError as e:
            if isinstance(e.cause, compat_HTTPError) and e.cause.code in (400, 401):
                error = json.loads(e.cause.read().decode())
                error_message = error.get('error_description') or error['details']
                raise ExtractorError('%s said: %s' % (
                    self.IE_NAME, error_message), expected=True)
            raise

        video_data = preplay['video']
        formats = self._extract_m3u8_formats(
            preplay['playURL'], video_id, 'mp4', 'm3u8_native')
        self._sort_formats(formats)
        episode = video_data.get('episode') or {}
        channel = video_data.get('channel') or {}
        season = video_data.get('season') or {}

        subtitles = {}
        for subtitle in preplay.get('subtitleURLs', []):
            cc_url = subtitle.get('url')
            if not cc_url:
                continue
            language_code = try_get(subtitle, lambda x: x['languages'][0]['language_code'], compat_str) or 'en'
            subtitles.setdefault(language_code, []).append({
                'url': cc_url,
            })

        return {
            'formats': formats,
            'id': video_id,
            'title': title,
            'description': clean_html(video.get('body')),
            'thumbnail': video.get('thumbnail_url'),
            'duration': int_or_none(video_data.get('video_duration')),
            'timestamp': int_or_none(video_data.get('created_at'), 1000),
            'age_limit': parse_age_limit(video_data.get('video_rating') or rating),
            'series': try_get(video_data, lambda x: x['show']['base']['display_title'], compat_str),
            'episode_number': int_or_none(episode.get('episode_number')),
            'episode_id': str_or_none(episode.get('id') or video_data.get('episode_id')),
            'season_number': int_or_none(season.get('season_number')),
            'season_id': str_or_none(season.get('id') or video_data.get('season_id')),
            'uploader': channel.get('name'),
            'uploader_id': str_or_none(channel.get('id')),
            'subtitles': subtitles,
        }