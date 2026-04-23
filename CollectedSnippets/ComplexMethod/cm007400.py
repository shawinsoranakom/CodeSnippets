def _real_extract(self, url):
        ptype, video_id = re.match(self._VALID_URL, url).groups()

        webpage = self._download_webpage(url, video_id, fatal=False) or ''
        props = (self._parse_json(self._search_regex(
            r'<script[^>]+id="__NEXT_DATA__"[^>]*>({.+?})</script>',
            webpage, 'next data', default='{}'), video_id,
            fatal=False) or {}).get('props') or {}
        player_api_cache = try_get(
            props, lambda x: x['initialReduxState']['playerApiCache']) or {}

        api_path, resp = None, {}
        for k, v in player_api_cache.items():
            if k.startswith('/episodes/') or k.startswith('/shortform/'):
                api_path, resp = k, v
                break
        else:
            episode_id = str_or_none(try_get(
                props, lambda x: x['pageProps']['episodeId']))
            api_path = '/%s/%s' % (self._PTYPE_MAP[ptype], episode_id or video_id)

        result = resp.get('results')
        if not result:
            resp = self._download_json(
                'https://player.api.stv.tv/v1' + api_path, video_id)
            result = resp['results']

        video = result['video']
        video_id = compat_str(video['id'])

        subtitles = {}
        _subtitles = result.get('_subtitles') or {}
        for ext, sub_url in _subtitles.items():
            subtitles.setdefault('en', []).append({
                'ext': 'vtt' if ext == 'webvtt' else ext,
                'url': sub_url,
            })

        programme = result.get('programme') or {}

        return {
            '_type': 'url_transparent',
            'id': video_id,
            'url': smuggle_url(self.BRIGHTCOVE_URL_TEMPLATE % video_id, {'geo_countries': ['GB']}),
            'description': result.get('summary'),
            'duration': float_or_none(video.get('length'), 1000),
            'subtitles': subtitles,
            'view_count': int_or_none(result.get('views')),
            'series': programme.get('name') or programme.get('shortName'),
            'ie_key': 'BrightcoveNew',
        }