def _extract_video(self, video_id, catalogue=None):
        # Videos are identified by idDiffusion so catalogue part is optional.
        # However when provided, some extra formats may be returned so we pass
        # it if available.
        info = self._download_json(
            'https://sivideo.webservices.francetelevisions.fr/tools/getInfosOeuvre/v2/',
            video_id, 'Downloading video JSON', query={
                'idDiffusion': video_id,
                'catalogue': catalogue or '',
            })

        if info.get('status') == 'NOK':
            raise ExtractorError(
                '%s returned error: %s' % (self.IE_NAME, info['message']),
                expected=True)
        allowed_countries = info['videos'][0].get('geoblocage')
        if allowed_countries:
            georestricted = True
            geo_info = self._download_json(
                'http://geo.francetv.fr/ws/edgescape.json', video_id,
                'Downloading geo restriction info')
            country = geo_info['reponse']['geo_info']['country_code']
            if country not in allowed_countries:
                raise ExtractorError(
                    'The video is not available from your location',
                    expected=True)
        else:
            georestricted = False

        def sign(manifest_url, manifest_id):
            for host in ('hdfauthftv-a.akamaihd.net', 'hdfauth.francetv.fr'):
                signed_url = url_or_none(self._download_webpage(
                    'https://%s/esi/TA' % host, video_id,
                    'Downloading signed %s manifest URL' % manifest_id,
                    fatal=False, query={
                        'url': manifest_url,
                    }))
                if signed_url:
                    return signed_url
            return manifest_url

        is_live = None

        videos = []

        for video in (info.get('videos') or []):
            if video.get('statut') != 'ONLINE':
                continue
            if not video.get('url'):
                continue
            videos.append(video)

        if not videos:
            for device_type in ['desktop', 'mobile']:
                fallback_info = self._download_json(
                    'https://player.webservices.francetelevisions.fr/v1/videos/%s' % video_id,
                    video_id, 'Downloading fallback %s video JSON' % device_type, query={
                        'device_type': device_type,
                        'browser': 'chrome',
                    }, fatal=False)

                if fallback_info and fallback_info.get('video'):
                    videos.append(fallback_info['video'])

        formats = []
        for video in videos:
            video_url = video.get('url')
            if not video_url:
                continue
            if is_live is None:
                is_live = (try_get(
                    video, lambda x: x['plages_ouverture'][0]['direct'], bool) is True
                    or video.get('is_live') is True
                    or '/live.francetv.fr/' in video_url)
            format_id = video.get('format')
            ext = determine_ext(video_url)
            if ext == 'f4m':
                if georestricted:
                    # See https://github.com/ytdl-org/youtube-dl/issues/3963
                    # m3u8 urls work fine
                    continue
                formats.extend(self._extract_f4m_formats(
                    sign(video_url, format_id) + '&hdcore=3.7.0&plugin=aasp-3.7.0.39.44',
                    video_id, f4m_id=format_id, fatal=False))
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    sign(video_url, format_id), video_id, 'mp4',
                    entry_protocol='m3u8_native', m3u8_id=format_id,
                    fatal=False))
            elif ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    sign(video_url, format_id), video_id, mpd_id=format_id, fatal=False))
            elif video_url.startswith('rtmp'):
                formats.append({
                    'url': video_url,
                    'format_id': 'rtmp-%s' % format_id,
                    'ext': 'flv',
                })
            else:
                if self._is_valid_url(video_url, video_id, format_id):
                    formats.append({
                        'url': video_url,
                        'format_id': format_id,
                    })

        self._sort_formats(formats)

        title = info['titre']
        subtitle = info.get('sous_titre')
        if subtitle:
            title += ' - %s' % subtitle
        title = title.strip()

        subtitles = {}
        subtitles_list = [{
            'url': subformat['url'],
            'ext': subformat.get('format'),
        } for subformat in info.get('subtitles', []) if subformat.get('url')]
        if subtitles_list:
            subtitles['fr'] = subtitles_list

        return {
            'id': video_id,
            'title': self._live_title(title) if is_live else title,
            'description': clean_html(info.get('synopsis')),
            'thumbnail': urljoin('https://sivideo.webservices.francetelevisions.fr', info.get('image')),
            'duration': int_or_none(info.get('real_duration')) or parse_duration(info.get('duree')),
            'timestamp': int_or_none(try_get(info, lambda x: x['diffusion']['timestamp'])),
            'is_live': is_live,
            'formats': formats,
            'subtitles': subtitles,
        }