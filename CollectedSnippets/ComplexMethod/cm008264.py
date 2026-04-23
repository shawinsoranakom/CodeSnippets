def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)

        nextjs_data = self._search_nextjs_v13_data(webpage, display_id)
        meta = get_first(nextjs_data, (
            lambda k, v: k in ('video', 'meta') and v['path'] == urllib.parse.urlparse(url).path))

        video_id = meta['uuid']
        info_dict = traverse_obj(meta, {
            'title': ('title', {str}),
            'description': ('description', {str.strip}),
        })

        if traverse_obj(meta, ('program', 'subtype')) != 'movie':
            for season_data in traverse_obj(nextjs_data, (..., 'playlists', ..., {dict})):
                episode_data = traverse_obj(season_data, ('videos', lambda _, v: v['videoId'] == video_id, any))
                if not episode_data:
                    continue

                season_number = traverse_obj(season_data, ('season', {int_or_none}))
                info_dict.update({
                    'episode': traverse_obj(episode_data, ('episodeTitle', {str})),
                    'episode_number': traverse_obj(episode_data, ('episodeNumber', {int_or_none})),
                    'season_number': season_number,
                    'series': self._search_regex(
                        fr'^(.+)? - S{season_number} - ', info_dict.get('title'), 'series', default=None),
                })
                break

        api = self._download_json(
            f'https://api.play.tv/web/v1/videos/long-form/{video_id}',
            video_id, headers={
                'Authorization': f'Bearer {self._id_token}',
                **self.geo_verification_headers(),
            })

        if 'manifestUrls' in api:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                api['manifestUrls']['hls'], video_id, ext='mp4', m3u8_id='HLS')

        else:
            if 'ssai' not in api:
                raise ExtractorError('expecting Google SSAI stream')

            ssai_content_source_id = api['ssai']['contentSourceID']
            ssai_video_id = api['ssai']['videoID']

            dai = self._download_json(
                f'https://dai.google.com/ondemand/dash/content/{ssai_content_source_id}/vid/{ssai_video_id}/streams',
                video_id, data=b'{"api-key":"null"}',
                headers={'content-type': 'application/json'})

            periods = self._extract_mpd_periods(dai['stream_manifest'], video_id)

            # skip pre-roll and mid-roll ads
            periods = [p for p in periods if '-ad-' not in p['id']]

            formats, subtitles = self._merge_mpd_periods(periods)

        info_dict.update({
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
        })
        return info_dict