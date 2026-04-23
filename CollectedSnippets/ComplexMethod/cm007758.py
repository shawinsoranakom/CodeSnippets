def _extract_video(self, video_info, video_id):
        is_live = dict_get(video_info, ('live', 'simulcast'), default=False)
        m3u8_protocol = 'm3u8' if is_live else 'm3u8_native'
        formats = []
        for vr in video_info['videoReferences']:
            player_type = vr.get('playerType') or vr.get('format')
            vurl = vr['url']
            ext = determine_ext(vurl)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    vurl, video_id,
                    ext='mp4', entry_protocol=m3u8_protocol,
                    m3u8_id=player_type, fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    vurl + '?hdcore=3.3.0', video_id,
                    f4m_id=player_type, fatal=False))
            elif ext == 'mpd':
                if player_type == 'dashhbbtv':
                    formats.extend(self._extract_mpd_formats(
                        vurl, video_id, mpd_id=player_type, fatal=False))
            else:
                formats.append({
                    'format_id': player_type,
                    'url': vurl,
                })
        rights = try_get(video_info, lambda x: x['rights'], dict) or {}
        if not formats and rights.get('geoBlockedSweden'):
            self.raise_geo_restricted(
                'This video is only available in Sweden',
                countries=self._GEO_COUNTRIES)
        self._sort_formats(formats)

        subtitles = {}
        subtitle_references = dict_get(video_info, ('subtitles', 'subtitleReferences'))
        if isinstance(subtitle_references, list):
            for sr in subtitle_references:
                subtitle_url = sr.get('url')
                subtitle_lang = sr.get('language', 'sv')
                if subtitle_url:
                    if determine_ext(subtitle_url) == 'm3u8':
                        # TODO(yan12125): handle WebVTT in m3u8 manifests
                        continue

                    subtitles.setdefault(subtitle_lang, []).append({'url': subtitle_url})

        title = video_info.get('title')

        series = video_info.get('programTitle')
        season_number = int_or_none(video_info.get('season'))
        episode = video_info.get('episodeTitle')
        episode_number = int_or_none(video_info.get('episodeNumber'))

        timestamp = unified_timestamp(rights.get('validFrom'))
        duration = int_or_none(dict_get(video_info, ('materialLength', 'contentDuration')))
        age_limit = None
        adult = dict_get(
            video_info, ('inappropriateForChildren', 'blockedForChildren'),
            skip_false_values=False)
        if adult is not None:
            age_limit = 18 if adult else 0

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'duration': duration,
            'timestamp': timestamp,
            'age_limit': age_limit,
            'series': series,
            'season_number': season_number,
            'episode': episode,
            'episode_number': episode_number,
            'is_live': is_live,
        }