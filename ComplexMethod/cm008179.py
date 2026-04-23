def _real_extract(self, url):
        display_id = self._match_valid_url(url).group('display_id')
        webpage = self._download_webpage(url, display_id)
        app_id = traverse_obj(
            self._search_json(r'window\.env\s*=', webpage, 'window env', display_id, default={}),
            ('TOP_AUTH_SERVICE_APP_ID', {str}))

        entries = []
        for player_data in traverse_obj(webpage, (
                {find_elements(tag='div', attr='data-component-name', value='video-player', html=True)},
                ..., {extract_attributes}, all, lambda _, v: v['data-media-id'])):
            media_id = player_data['data-media-id']
            parent_uri = player_data.get('data-video-resource-parent-uri')
            formats, subtitles = [], {}

            video_data = {}
            if parent_uri:
                video_data = self._download_json(
                    'https://fave.api.cnn.io/v1/video', media_id, fatal=False,
                    query={
                        'id': media_id,
                        'stellarUri': parent_uri,
                    })
                for direct_url in traverse_obj(video_data, ('files', ..., 'fileUri', {url_or_none})):
                    resolution, bitrate = None, None
                    if mobj := re.search(r'-(?P<res>\d+x\d+)_(?P<tbr>\d+)k\.mp4', direct_url):
                        resolution, bitrate = mobj.group('res', 'tbr')
                    formats.append({
                        'url': direct_url,
                        'format_id': 'direct',
                        'quality': 1,
                        'tbr': int_or_none(bitrate),
                        **parse_resolution(resolution),
                    })
                for sub_data in traverse_obj(video_data, (
                        'closedCaptions', 'types', lambda _, v: url_or_none(v['track']['url']), 'track')):
                    subtitles.setdefault(sub_data.get('lang') or 'en', []).append({
                        'url': sub_data['url'],
                        'name': sub_data.get('label'),
                    })

            if app_id:
                media_data = self._download_json(
                    f'https://medium.ngtv.io/v2/media/{media_id}/desktop', media_id, fatal=False,
                    query={'appId': app_id})
                m3u8_url = traverse_obj(media_data, (
                    'media', 'desktop', 'unprotected', 'unencrypted', 'url', {url_or_none}))
                if m3u8_url:
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(
                        m3u8_url, media_id, 'mp4', m3u8_id='hls', fatal=False)
                    formats.extend(fmts)
                    self._merge_subtitles(subs, target=subtitles)

            entries.append({
                **traverse_obj(player_data, {
                    'title': ('data-headline', {clean_html}),
                    'description': ('data-description', {clean_html}),
                    'duration': ('data-duration', {parse_duration}),
                    'timestamp': ('data-publish-date', {parse_iso8601}),
                    'thumbnail': (
                        'data-poster-image-override', {json.loads}, 'big', 'uri', {url_or_none},
                        {update_url(query='c=original')}),
                    'display_id': 'data-video-slug',
                }),
                **traverse_obj(video_data, {
                    'timestamp': ('dateCreated', 'uts', {int_or_none(scale=1000)}),
                    'description': ('description', {clean_html}),
                    'title': ('headline', {str}),
                    'modified_timestamp': ('lastModified', 'uts', {int_or_none(scale=1000)}),
                    'duration': ('trt', {int_or_none}),
                }),
                'id': media_id,
                'formats': formats,
                'subtitles': subtitles,
            })

        if len(entries) == 1:
            return {
                **entries[0],
                'display_id': display_id,
            }

        return self.playlist_result(entries, display_id)