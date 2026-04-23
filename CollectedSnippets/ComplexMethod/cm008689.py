def _extract_video(self, video_id, hostname=None):
        is_live = None
        videos = []
        drm_formats = False
        title = None
        subtitle = None
        episode_number = None
        season_number = None
        image = None
        duration = None
        timestamp = None
        spritesheets = None

        # desktop+chrome returns dash; mobile+safari returns hls
        for device_type, browser in [('desktop', 'chrome'), ('mobile', 'safari')]:
            dinfo = self._download_json(
                f'https://k7.ftven.fr/videos/{video_id}', video_id,
                f'Downloading {device_type} {browser} video JSON', query=filter_dict({
                    'device_type': device_type,
                    'browser': browser,
                    'domain': hostname,
                }), fatal=False, expected_status=422)  # 422 json gives detailed error code/message

            if not dinfo:
                continue

            if video := traverse_obj(dinfo, ('video', {dict})):
                videos.append(video)
                if duration is None:
                    duration = video.get('duration')
                if is_live is None:
                    is_live = video.get('is_live')
                if spritesheets is None:
                    spritesheets = video.get('spritesheets')
            elif code := traverse_obj(dinfo, ('code', {int})):
                if code == 2009:
                    self.raise_geo_restricted(countries=self._GEO_COUNTRIES)
                elif code in (2015, 2017, 2019):
                    # 2015: L'accès à cette vidéo est impossible. (DRM-only)
                    # 2017: Cette vidéo n'est pas disponible depuis le site web mobile (b/c DRM)
                    # 2019: L'accès à cette vidéo est incompatible avec votre configuration. (DRM-only)
                    drm_formats = True
                    continue
                self.report_warning(
                    f'{self.IE_NAME} said: {code} "{clean_html(dinfo.get("message"))}"')
                continue

            if meta := traverse_obj(dinfo, ('meta', {dict})):
                if title is None:
                    title = meta.get('title')
                # meta['pre_title'] contains season and episode number for series in format "S<ID> E<ID>"
                season_number, episode_number = self._search_regex(
                    r'S(\d+)\s*E(\d+)', meta.get('pre_title'), 'episode info', group=(1, 2), default=(None, None))
                if subtitle is None:
                    subtitle = meta.get('additional_title')
                if image is None:
                    image = meta.get('image_url')
                if timestamp is None:
                    timestamp = parse_iso8601(meta.get('broadcasted_at'))

        if not videos and drm_formats:
            self.report_drm(video_id)

        formats, subtitles, video_url = [], {}, None
        for video in traverse_obj(videos, lambda _, v: url_or_none(v['url'])):
            video_url = video['url']
            format_id = video.get('format')

            if token_url := traverse_obj(video, ('token', (None, 'akamai'), {url_or_none}, any)):
                tokenized_url = traverse_obj(self._download_json(
                    token_url, video_id, f'Downloading signed {format_id} manifest URL',
                    fatal=False, query={
                        'format': 'json',
                        'url': video_url,
                    }), ('url', {url_or_none}))
                if tokenized_url:
                    video_url = tokenized_url

            ext = determine_ext(video_url)
            if ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    video_url, video_id, f4m_id=format_id or ext, fatal=False))
            elif ext == 'm3u8':
                format_id = format_id or 'hls'
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    video_url, video_id, 'mp4', m3u8_id=format_id, fatal=False)
                for f in traverse_obj(fmts, lambda _, v: v['vcodec'] == 'none' and v.get('tbr') is None):
                    if mobj := re.match(rf'{format_id}-[Aa]udio-\w+-(?P<bitrate>\d+)', f['format_id']):
                        f.update({
                            'tbr': int_or_none(mobj.group('bitrate')),
                            'acodec': 'mp4a',
                        })
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            elif ext == 'mpd':
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    video_url, video_id, mpd_id=format_id or 'dash', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            elif video_url.startswith('rtmp'):
                formats.append({
                    'url': video_url,
                    'format_id': join_nonempty('rtmp', format_id),
                    'ext': 'flv',
                })
            else:
                if self._is_valid_url(video_url, video_id, format_id):
                    formats.append({
                        'url': video_url,
                        'format_id': format_id,
                    })

            # XXX: what is video['captions']?

        if not formats and video_url:
            urlh = self._request_webpage(
                HEADRequest(video_url), video_id, 'Checking for geo-restriction',
                fatal=False, expected_status=403)
            if urlh and urlh.headers.get('x-errortype') == 'geo':
                self.raise_geo_restricted(countries=self._GEO_COUNTRIES, metadata_available=True)

        for f in formats:
            if f.get('acodec') != 'none' and f.get('language') in ('qtz', 'qad'):
                f['language_preference'] = -10
                f['format_note'] = 'audio description{}'.format(format_field(f, 'format_note', ', %s'))

        if spritesheets:
            formats.append({
                'format_id': 'spritesheets',
                'format_note': 'storyboard',
                'acodec': 'none',
                'vcodec': 'none',
                'ext': 'mhtml',
                'protocol': 'mhtml',
                'url': 'about:invalid',
                'fragments': [{
                    'url': sheet,
                    # XXX: not entirely accurate; each spritesheet seems to be
                    # a 10x10 grid of thumbnails corresponding to approximately
                    # 2 seconds of the video; the last spritesheet may be shorter
                    'duration': 200,
                } for sheet in traverse_obj(spritesheets, (..., {url_or_none}))],
            })

        return {
            'id': video_id,
            'title': join_nonempty(title, subtitle, delim=' - ').strip(),
            'thumbnail': image,
            'duration': duration,
            'timestamp': timestamp,
            'is_live': is_live,
            'formats': formats,
            'subtitles': subtitles,
            'episode': subtitle if episode_number else None,
            'series': title if episode_number else None,
            'episode_number': int_or_none(episode_number),
            'season_number': int_or_none(season_number),
            '_format_sort_fields': ('res', 'tbr', 'proto'),  # prioritize m3u8 over dash
        }