def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('sid') or mobj.group('id')
        partner_id = mobj.group('partner_id') or compat_parse_qs(compat_urllib_parse_urlparse(url).query).get('partner_id', [None])[0] or '97'

        item = self._download_json(
            'https://siren.more.tv/player/config', video_id, query={
                'partner_id': partner_id,
                'track_id': video_id,
            })['data']['playlist']['items'][0]

        title = item.get('title')
        series = item.get('project_name')
        season = item.get('season_name')
        episode = item.get('episode_name')
        if not title:
            title = []
            for v in (series, season, episode):
                if v:
                    title.append(v)
            title = ' '.join(title)

        streams = item.get('streams') or []
        for protocol in ('DASH', 'HLS'):
            stream_url = item.get(protocol.lower() + '_url')
            if stream_url:
                streams.append({'protocol': protocol, 'url': stream_url})

        formats = []
        for stream in streams:
            stream_url = stream.get('url')
            if not stream_url:
                continue
            protocol = stream.get('protocol')
            if protocol == 'DASH':
                formats.extend(self._extract_mpd_formats(
                    stream_url, video_id, mpd_id='dash', fatal=False))
            elif protocol == 'HLS':
                formats.extend(self._extract_m3u8_formats(
                    stream_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id='hls', fatal=False))
            elif protocol == 'MSS':
                formats.extend(self._extract_ism_formats(
                    stream_url, video_id, ism_id='mss', fatal=False))

        if not formats:
            error = item.get('error')
            if error:
                if error in ('Данное видео недоступно для просмотра на территории этой страны', 'Данное видео доступно для просмотра только на территории России'):
                    self.raise_geo_restricted(countries=['RU'])
                raise ExtractorError(error, expected=True)
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'series': series,
            'season': season,
            'episode': episode,
            'thumbnail': item.get('thumbnail_url'),
            'duration': int_or_none(item.get('duration')),
            'view_count': int_or_none(item.get('views')),
            'age_limit': int_or_none(item.get('min_age')),
            'formats': formats,
        }