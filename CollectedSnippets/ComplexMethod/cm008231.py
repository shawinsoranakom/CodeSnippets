def _real_extract(self, url):
        video_id = self._match_id(url)
        ac_idx = parse_qs(url).get('ac', [None])[-1]
        video_id = f'{video_id}{format_field(ac_idx, None, "__%s")}'

        webpage = self._download_webpage(url, video_id)
        json_bangumi_data = self._search_json(r'window.bangumiData\s*=', webpage, 'bangumiData', video_id)

        if ac_idx:
            video_info = json_bangumi_data['hlVideoInfo']
            return {
                **self._extract_metadata(video_id, video_info),
                'title': video_info.get('title'),
            }

        video_info = json_bangumi_data['currentVideoInfo']

        season_id = json_bangumi_data.get('bangumiId')
        season_number = season_id and next((
            idx for idx, v in enumerate(json_bangumi_data.get('relatedBangumis') or [], 1)
            if v.get('id') == season_id), 1)

        json_bangumi_list = self._search_json(
            r'window\.bangumiList\s*=', webpage, 'bangumiList', video_id, fatal=False)
        video_internal_id = int_or_none(traverse_obj(json_bangumi_data, ('currentVideoInfo', 'id')))
        episode_number = video_internal_id and next((
            idx for idx, v in enumerate(json_bangumi_list.get('items') or [], 1)
            if v.get('videoId') == video_internal_id), None)

        return {
            **self._extract_metadata(video_id, video_info),
            'title': json_bangumi_data.get('showTitle'),
            'thumbnail': json_bangumi_data.get('image'),
            'season': json_bangumi_data.get('bangumiTitle'),
            'season_id': str_or_none(season_id),
            'season_number': season_number,
            'episode': json_bangumi_data.get('title'),
            'episode_number': episode_number,
            'comment_count': int_or_none(json_bangumi_data.get('commentCount')),
        }