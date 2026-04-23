def _real_extract(self, url):
        domain, film_id = self._match_valid_url(url).groups()
        site = domain.split('.')[-2]
        if site in self._SITE_MAP:
            site = self._SITE_MAP[site]

        content_data = self._call_api(
            site, 'entitlement/video/status', film_id, url, {
                'id': film_id,
            })['video']
        gist = content_data['gist']
        title = gist['title']
        video_assets = content_data['streamingInfo']['videoAssets']

        hls_url = video_assets.get('hls')
        formats, subtitles = [], {}
        if hls_url:
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                hls_url, film_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False)

        for video_asset in video_assets.get('mpeg') or []:
            video_asset_url = video_asset.get('url')
            if not video_asset_url:
                continue
            bitrate = int_or_none(video_asset.get('bitrate'))
            height = int_or_none(self._search_regex(
                r'^_?(\d+)[pP]$', video_asset.get('renditionValue'),
                'height', default=None))
            formats.append({
                'url': video_asset_url,
                'format_id': join_nonempty('http', bitrate),
                'tbr': bitrate,
                'height': height,
                'vcodec': video_asset.get('codec'),
            })

        subs = {}
        for sub in traverse_obj(content_data, ('contentDetails', 'closedCaptions')) or []:
            sub_url = sub.get('url')
            if not sub_url:
                continue
            subs.setdefault(sub.get('language', 'English'), []).append({
                'url': sub_url,
            })

        return {
            'id': film_id,
            'title': title,
            'description': gist.get('description'),
            'thumbnail': gist.get('videoImageUrl'),
            'duration': int_or_none(gist.get('runtime')),
            'age_limit': parse_age_limit(content_data.get('parentalRating')),
            'timestamp': int_or_none(gist.get('publishDate'), 1000),
            'formats': formats,
            'subtitles': self._merge_subtitles(subs, subtitles),
            'categories': traverse_obj(content_data, ('categories', ..., 'title')),
            'tags': traverse_obj(content_data, ('tags', ..., 'title')),
        }