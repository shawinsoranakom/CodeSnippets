def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        # now quite different params!
        params = extract_attributes(self._search_regex(
            r'''(<[^>]+\b(?:class|data-testid)\s*=\s*("|')genie-container\2[^>]*>)''',
            webpage, 'params'))

        ios_playlist_url = traverse_obj(
            params, 'data-video-id', 'data-video-playlist',
            get_all=False, expected_type=url_or_none)

        headers = self.geo_verification_headers()
        headers.update({
            'Accept': 'application/vnd.itv.vod.playlist.v2+json',
            'Content-Type': 'application/json',
        })
        ios_playlist = self._download_json(
            ios_playlist_url, video_id, data=json.dumps({
                'user': {
                    'entitlements': [],
                },
                'device': {
                    'manufacturer': 'Mobile Safari',
                    'model': '5.1',
                    'os': {
                        'name': 'iOS',
                        'version': '5.0',
                        'type': ' mobile'
                    }
                },
                'client': {
                    'version': '4.1',
                    'id': 'browser',
                    'supportsAdPods': True,
                    'service': 'itv.x',
                    'appversion': '2.43.28',
                },
                'variantAvailability': {
                    'player': 'hls',
                    'featureset': {
                        'min': ['hls', 'aes', 'outband-webvtt'],
                        'max': ['hls', 'aes', 'outband-webvtt']
                    },
                    'platformTag': 'mobile'
                }
            }).encode(), headers=headers)
        video_data = ios_playlist['Playlist']['Video']
        ios_base_url = traverse_obj(video_data, 'Base', expected_type=url_or_none)

        media_url = (
            (lambda u: url_or_none(urljoin(ios_base_url, u)))
            if ios_base_url else url_or_none)

        formats = []
        for media_file in traverse_obj(video_data, 'MediaFiles', expected_type=list) or []:
            href = traverse_obj(media_file, 'Href', expected_type=media_url)
            if not href:
                continue
            ext = determine_ext(href)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    href, video_id, 'mp4', entry_protocol='m3u8',
                    m3u8_id='hls', fatal=False))

            else:
                formats.append({
                    'url': href,
                })
        self._sort_formats(formats)
        for f in formats:
            f.setdefault('http_headers', {})
            f['http_headers'].update(self._vanilla_ua_header())

        subtitles = {}
        for sub in traverse_obj(video_data, 'Subtitles', expected_type=list) or []:
            href = traverse_obj(sub, 'Href', expected_type=url_or_none)
            if not href:
                continue
            subtitles.setdefault('en', []).append({
                'url': href,
                'ext': determine_ext(href, 'vtt'),
            })

        next_data = self._search_nextjs_data(webpage, video_id, fatal=False, default={})
        video_data.update(traverse_obj(next_data, ('props', 'pageProps', ('title', 'episode')), expected_type=dict)[0] or {})
        title = traverse_obj(video_data, 'headerTitle', 'episodeTitle')
        info = self._og_extract(webpage, require_title=not title)
        tn = info.pop('thumbnail', None)
        if tn:
            info['thumbnails'] = [{'url': tn}]

        # num. episode title
        num_ep_title = video_data.get('numberedEpisodeTitle')
        if not num_ep_title:
            num_ep_title = clean_html(get_element_by_attribute('data-testid', 'episode-hero-description-strong', webpage))
            num_ep_title = num_ep_title and num_ep_title.rstrip(' -')
        ep_title = strip_or_none(
            video_data.get('episodeTitle')
            or (num_ep_title.split('.', 1)[-1] if num_ep_title else None))
        title = title or re.sub(r'\s+-\s+ITVX$', '', info['title'])
        if ep_title and ep_title != title:
            title = title + ' - ' + ep_title

        def get_thumbnails():
            tns = []
            for w, x in (traverse_obj(video_data, ('imagePresets'), expected_type=dict) or {}).items():
                if isinstance(x, dict):
                    for y, z in x.items():
                        tns.append({'id': w + '_' + y, 'url': z})
            return tns or None

        video_str = lambda *x: traverse_obj(
            video_data, *x, get_all=False, expected_type=strip_or_none)

        return merge_dicts({
            'id': video_id,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            # parsing hh:mm:ss:nnn not yet patched
            'duration': parse_duration(re.sub(r'(\d{2})(:)(\d{3}$)', r'\1.\3', video_data.get('Duration') or '')),
            'description': video_str('synopsis'),
            'timestamp': traverse_obj(video_data, 'broadcastDateTime', 'dateTime', expected_type=parse_iso8601),
            'thumbnails': get_thumbnails(),
            'series': video_str('showTitle', 'programmeTitle'),
            'series_number': int_or_none(video_data.get('seriesNumber')),
            'episode': ep_title,
            'episode_number': int_or_none((num_ep_title or '').split('.')[0]),
            'channel': video_str('channel'),
            'categories': traverse_obj(video_data, ('categories', 'formatted'), expected_type=list),
            'age_limit': {False: 16, True: 0}.get(video_data.get('isChildrenCategory')),
        }, info)