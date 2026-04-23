def _real_extract(self, url):
        episode_id = self._match_id(url)
        headers = self.geo_verification_headers()
        webpage = self._download_webpage(url, episode_id, headers=headers)

        if '您所在的地区无法观看本片' in webpage:
            raise GeoRestrictedError('This video is restricted')
        elif '正在观看预览，大会员免费看全片' in webpage:
            self.raise_login_required('This video is for premium members only')

        headers['Referer'] = url

        play_info = (
            self._search_json(
                r'playurlSSRData\s*=', webpage, 'embedded page info', episode_id,
                end_pattern='\n', default=None)
            or self._download_json(
                'https://api.bilibili.com/pgc/player/web/v2/playurl', episode_id,
                'Extracting episode', query={'fnval': 12240, 'ep_id': episode_id},
                headers=headers))

        # play_info can be structured in at least three different ways, e.g.:
        # 1.) play_info['result']['video_info'] and play_info['code']
        # 2.) play_info['raw']['data']['video_info'] and play_info['code']
        # 3.) play_info['data']['result']['video_info'] and play_info['data']['code']
        # So we need to transform any of the above into a common structure
        status_code = play_info.get('code')
        if 'raw' in play_info:
            play_info = play_info['raw']
        if 'data' in play_info:
            play_info = play_info['data']
        if status_code is None:
            status_code = play_info.get('code')
        if 'result' in play_info:
            play_info = play_info['result']

        geo_blocked = traverse_obj(play_info, (
            'plugins', lambda _, v: v['name'] == 'AreaLimitPanel', 'config', 'is_block', {bool}, any))
        premium_only = status_code == -10403

        video_info = traverse_obj(play_info, ('video_info', {dict})) or {}
        formats = self.extract_formats(video_info)

        if not formats:
            if geo_blocked:
                self.raise_geo_restricted()
            elif premium_only or '成为大会员抢先看' in webpage or '开通大会员观看' in webpage:
                self.raise_login_required('This video is for premium members only')

        if traverse_obj(play_info, ((
            ('play_check', 'play_detail'),  # 'PLAY_PREVIEW' vs 'PLAY_WHOLE' vs 'PLAY_NONE'
            'play_video_type',              # 'preview' vs 'whole' vs 'none'
        ), any, {lambda x: x in ('PLAY_PREVIEW', 'preview')})):
            self.report_warning(
                'Only preview format is available, '
                f'you have to become a premium member to access full video. {self._login_hint()}')

        bangumi_info = self._download_json(
            'https://api.bilibili.com/pgc/view/web/season', episode_id, 'Get episode details',
            query={'ep_id': episode_id}, headers=headers)['result']

        episode_number, episode_info = next((
            (idx, ep) for idx, ep in enumerate(traverse_obj(
                bangumi_info, (('episodes', ('section', ..., 'episodes')), ..., {dict})), 1)
            if str_or_none(ep.get('id')) == episode_id), (1, {}))

        season_id = bangumi_info.get('season_id')
        season_number, season_title = season_id and next((
            (idx + 1, e.get('season_title')) for idx, e in enumerate(
                traverse_obj(bangumi_info, ('seasons', ...)))
            if e.get('season_id') == season_id
        ), (None, None))

        aid = episode_info.get('aid')

        return {
            'id': episode_id,
            'formats': formats,
            **traverse_obj(bangumi_info, {
                'series': ('series', 'series_title', {str}),
                'series_id': ('series', 'series_id', {str_or_none}),
                'thumbnail': ('square_cover', {url_or_none}),
            }),
            **traverse_obj(episode_info, {
                'episode': ('long_title', {str}),
                'episode_number': ('title', {int_or_none}, {lambda x: x or episode_number}),
                'timestamp': ('pub_time', {int_or_none}),
                'title': {lambda v: v and join_nonempty('title', 'long_title', delim=' ', from_dict=v)},
            }),
            'episode_id': episode_id,
            'season': str_or_none(season_title),
            'season_id': str_or_none(season_id),
            'season_number': season_number,
            'duration': float_or_none(video_info.get('timelength'), scale=1000),
            'subtitles': self.extract_subtitles(episode_id, episode_info.get('cid'), aid=aid),
            '__post_extractor': self.extract_comments(aid),
            'http_headers': {'Referer': url},
        }