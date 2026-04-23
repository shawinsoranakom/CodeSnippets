def _real_extract(self, url):
        asin = f'amzn1.dv.gti.{self._match_id(url)}'
        prs = self._call_api(asin, note='Downloading playback info')

        formats, subtitles = [], {}
        for type_, asset in prs['playbackAssets'].items():
            if not traverse_obj(asset, 'manifestUrl'):
                continue
            if type_ == 'hls':
                m3u8_fmts, m3u8_subs = self._extract_m3u8_formats_and_subtitles(
                    asset['manifestUrl'], asin, ext='mp4', entry_protocol='m3u8_native',
                    m3u8_id=type_, fatal=False)
                formats.extend(m3u8_fmts)
                subtitles = self._merge_subtitles(subtitles, m3u8_subs)
            elif type_ == 'dash':
                mpd_fmts, mpd_subs = self._extract_mpd_formats_and_subtitles(
                    asset['manifestUrl'], asin, mpd_id=type_, fatal=False)
                formats.extend(mpd_fmts)
                subtitles = self._merge_subtitles(subtitles, mpd_subs)
            else:
                self.report_warning(f'Unknown asset type: {type_}')

        title_info = self._call_api(
            asin, note='Downloading title info', data={
                'operationName': 'content',
                'variables': {'contentId': asin},
                'query': self._GRAPHQL_QUERY_CONTENT,
            })
        credits_time = try_get(title_info, lambda x: x['timecode']['endCreditsTime'] / 1000)
        is_episode = title_info.get('vodType') == 'EPISODE'

        return {
            'id': asin,
            'title': title_info.get('name'),
            'formats': formats,
            'subtitles': subtitles,
            'language': traverse_obj(title_info, ('audioTracks', 0)),
            'thumbnails': [{
                'id': type_,
                'url': url,
            } for type_, url in (title_info.get('images') or {}).items()],
            'description': traverse_obj(title_info, ('description', 'synopsis')),
            'release_timestamp': int_or_none(try_get(title_info, lambda x: x['publicReleaseDateUTC'] / 1000)),
            'duration': traverse_obj(title_info, ('description', 'contentLengthInSeconds')),
            'chapters': [{
                'start_time': credits_time,
                'title': 'End Credits',
            }] if credits_time else [],
            'series': title_info.get('seriesName'),
            'series_id': title_info.get('seriesId'),
            'season_number': title_info.get('seasonNumber'),
            'season_id': title_info.get('seasonId'),
            'episode': title_info.get('name') if is_episode else None,
            'episode_number': title_info.get('episodeNumber'),
            'episode_id': asin if is_episode else None,
        }