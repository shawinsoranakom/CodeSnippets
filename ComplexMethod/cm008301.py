def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        display_id = mobj.group('id')
        site = mobj.group('site')

        webpage = self._download_webpage(url, display_id)

        description = clean_html(self._og_search_description(webpage, default=None))
        if site == 'novaplus':
            upload_date = unified_strdate(self._search_regex(
                r'(\d{1,2}-\d{1,2}-\d{4})$', display_id, 'upload date', default=None))
        elif site == 'fanda':
            upload_date = unified_strdate(self._search_regex(
                r'<span class="date_time">(\d{1,2}\.\d{1,2}\.\d{4})', webpage, 'upload date', default=None))
        else:
            upload_date = None

        # novaplus
        embed_id = self._search_regex(
            r'<iframe[^>]+\bsrc=["\'](?:https?:)?//media(?:tn)?\.cms\.nova\.cz/embed/([^/?#&"\']+)',
            webpage, 'embed url', default=None)
        if embed_id:
            return {
                '_type': 'url_transparent',
                'url': f'https://media.cms.nova.cz/embed/{embed_id}',
                'ie_key': NovaEmbedIE.ie_key(),
                'id': embed_id,
                'description': description,
                'upload_date': upload_date,
            }

        video_id = self._search_regex(
            [r"(?:media|video_id)\s*:\s*'(\d+)'",
             r'media=(\d+)',
             r'id="article_video_(\d+)"',
             r'id="player_(\d+)"'],
            webpage, 'video id')

        config_url = self._search_regex(
            r'src="(https?://(?:tn|api)\.nova\.cz/bin/player/videojs/config\.php\?[^"]+)"',
            webpage, 'config url', default=None)
        config_params = {}

        if not config_url:
            player = self._parse_json(
                self._search_regex(
                    r'(?s)Player\s*\(.+?\s*,\s*({.+?\bmedia\b["\']?\s*:\s*["\']?\d+.+?})\s*\)', webpage,
                    'player', default='{}'),
                video_id, transform_source=js_to_json, fatal=False)
            if player:
                config_url = url_or_none(player.get('configUrl'))
                params = player.get('configParams')
                if isinstance(params, dict):
                    config_params = params

        if not config_url:
            DEFAULT_SITE_ID = '23000'
            SITES = {
                'tvnoviny': DEFAULT_SITE_ID,
                'novaplus': DEFAULT_SITE_ID,
                'vymena': DEFAULT_SITE_ID,
                'krasna': DEFAULT_SITE_ID,
                'fanda': '30',
                'tn': '30',
                'doma': '30',
            }

            site_id = self._search_regex(
                r'site=(\d+)', webpage, 'site id', default=None) or SITES.get(
                site, DEFAULT_SITE_ID)

            config_url = 'https://api.nova.cz/bin/player/videojs/config.php'
            config_params = {
                'site': site_id,
                'media': video_id,
                'quality': 3,
                'version': 1,
            }

        config = self._download_json(
            config_url, display_id,
            'Downloading config JSON', query=config_params,
            transform_source=lambda s: s[s.index('{'):s.rindex('}') + 1])

        mediafile = config['mediafile']
        video_url = mediafile['src']

        m = re.search(r'^(?P<url>rtmpe?://[^/]+/(?P<app>[^/]+?))/&*(?P<playpath>.+)$', video_url)
        if m:
            formats = [{
                'url': m.group('url'),
                'app': m.group('app'),
                'play_path': m.group('playpath'),
                'player_path': 'http://tvnoviny.nova.cz/static/shared/app/videojs/video-js.swf',
                'ext': 'flv',
            }]
        else:
            formats = [{
                'url': video_url,
            }]

        title = mediafile.get('meta', {}).get('title') or self._og_search_title(webpage)
        thumbnail = config.get('poster')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'upload_date': upload_date,
            'thumbnail': thumbnail,
            'formats': formats,
        }