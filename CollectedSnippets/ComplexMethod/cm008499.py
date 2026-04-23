def _real_extract(self, url):
        video_id = self._match_id(url)

        # it could be anything that is a valid JS function name
        callback = random.choice((
            'jebac_pis',
            'jebacpis',
            'ziobro',
            'sasin70',
            'sasin_przejebal_70_milionow_PLN',
            'tvp_is_a_state_propaganda_service',
        ))

        webpage = self._download_webpage(
            f'https://www.tvp.pl/sess/TVPlayer2/api.php?id={video_id}&@method=getTvpConfig&@callback={callback}', video_id)

        # stripping JSONP padding
        datastr = webpage[15 + len(callback):-3]
        if datastr.startswith('null,'):
            error = self._parse_json(datastr[5:], video_id, fatal=False)
            error_desc = traverse_obj(error, (0, 'desc'))

            if error_desc == 'Obiekt wymaga płatności':
                raise ExtractorError('Video requires payment and log-in, but log-in is not implemented')

            raise ExtractorError(error_desc or 'unexpected JSON error')

        content = self._parse_json(datastr, video_id)['content']
        info = content['info']
        is_live = try_get(info, lambda x: x['isLive'], bool)

        if info.get('isGeoBlocked'):
            # actual country list is not provided, we just assume it's always available in PL
            self.raise_geo_restricted(countries=['PL'])

        formats = []
        for file in content['files']:
            video_url = url_or_none(file.get('url'))
            if not video_url:
                continue
            ext = determine_ext(video_url, None)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(video_url, video_id, m3u8_id='hls', fatal=False, live=is_live))
            elif ext == 'mpd':
                if is_live:
                    # doesn't work with either ffmpeg or native downloader
                    continue
                formats.extend(self._extract_mpd_formats(video_url, video_id, mpd_id='dash', fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(video_url, video_id, f4m_id='hds', fatal=False))
            elif video_url.endswith('.ism/manifest'):
                formats.extend(self._extract_ism_formats(video_url, video_id, ism_id='mss', fatal=False))
            else:
                formats.append({
                    'format_id': 'direct',
                    'url': video_url,
                    'ext': ext or file.get('type'),
                    'fps': int_or_none(traverse_obj(file, ('quality', 'fps'))),
                    'tbr': int_or_none(traverse_obj(file, ('quality', 'bitrate')), scale=1000),
                    'width': int_or_none(traverse_obj(file, ('quality', 'width'))),
                    'height': int_or_none(traverse_obj(file, ('quality', 'height'))),
                })

        title = dict_get(info, ('subtitle', 'title', 'seoTitle'))
        description = dict_get(info, ('description', 'seoDescription'))
        thumbnails = []
        for thumb in content.get('posters') or ():
            thumb_url = thumb.get('src')
            if not thumb_url or '{width}' in thumb_url or '{height}' in thumb_url:
                continue
            thumbnails.append({
                'url': thumb.get('src'),
                'width': thumb.get('width'),
                'height': thumb.get('height'),
            })
        age_limit = try_get(info, lambda x: x['ageGroup']['minAge'], int)
        if age_limit == 1:
            age_limit = 0
        duration = try_get(info, lambda x: x['duration'], int) if not is_live else None

        subtitles = {}
        for sub in content.get('subtitles') or []:
            if not sub.get('url'):
                continue
            subtitles.setdefault(sub['lang'], []).append({
                'url': sub['url'],
                'ext': sub.get('type'),
            })

        info_dict = {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnails': thumbnails,
            'age_limit': age_limit,
            'is_live': is_live,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
        }

        # vod.tvp.pl
        if info.get('vortalName') == 'vod':
            info_dict.update({
                'title': '{}, {}'.format(info.get('title'), info.get('subtitle')),
                'series': info.get('title'),
                'season': info.get('season'),
                'episode_number': info.get('episode'),
            })

        return info_dict