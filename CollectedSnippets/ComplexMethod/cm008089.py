def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id, fatal=False)

        player_url = None
        query = {}
        if webpage:
            player_url = self._search_regex(
                r'player\.init\s*\(\s*(["\'])(?P<url>(?:(?!\1).)+)\1', webpage,
                'player url', default=None, group='url')

        if not player_url:
            player_url = f'http://api.yapfiles.ru/load/{video_id}/'
            query = {
                'md5': 'ded5f369be61b8ae5f88e2eeb2f3caff',
                'type': 'json',
                'ref': url,
            }

        player = self._download_json(
            player_url, video_id, query=query)['player']

        playlist_url = player['playlist']
        title = player['title']
        thumbnail = player.get('poster')

        if title == 'Ролик удален' or 'deleted.jpg' in (thumbnail or ''):
            raise ExtractorError(
                f'Video {video_id} has been removed', expected=True)

        playlist = self._download_json(
            playlist_url, video_id)['player']['main']

        hd_height = int_or_none(player.get('hd'))

        QUALITIES = ('sd', 'hd')
        quality_key = qualities(QUALITIES)
        formats = []
        for format_id in QUALITIES:
            is_hd = format_id == 'hd'
            format_url = url_or_none(playlist.get(
                'file%s' % ('_hd' if is_hd else '')))
            if not format_url:
                continue
            formats.append({
                'url': format_url,
                'format_id': format_id,
                'quality': quality_key(format_id),
                'height': hd_height if is_hd else None,
            })

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': int_or_none(player.get('length')),
            'formats': formats,
        }