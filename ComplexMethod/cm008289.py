def _real_extract(self, url):
        site, display_id = self._match_valid_url(url).group('site', 'id')
        webpage = self._download_webpage(url, display_id)
        config = self._extract_global_var('__CONFIG__', webpage, display_id)
        data = self._extract_global_var(config['globalVar'], webpage, display_id)
        video_id = traverse_obj(data, (
            'page', 'content', 'video', 'layout', (('video', 'id'), 'videoid'), {str}, any))
        if not video_id:
            video_id = self._search_regex([
                # data-track-video_id="VDKA39492078"
                # data-track-video_id_code="vdka39492078"
                # data-video-id="'VDKA3609139'"
                r'data-(?:track-)?video[_-]id(?:_code)?=["\']*((?:vdka|VDKA)\d+)',
                # page.analytics.videoIdCode
                r'\bvideoIdCode["\']\s*:\s*["\']((?:vdka|VDKA)\d+)'], webpage, 'video ID')

        site_info = self._SITE_INFO[site]
        brand = site_info['brand']
        video_data = self._extract_videos(brand, video_id)[0]
        video_id = video_data['id']
        title = video_data['title']

        formats = []
        subtitles = {}
        for asset in video_data.get('assets', {}).get('asset', []):
            asset_url = asset.get('value')
            if not asset_url:
                continue
            format_id = asset.get('format')
            ext = determine_ext(asset_url)
            if ext == 'm3u8':
                video_type = video_data.get('type')
                data = {
                    'video_id': video_id,
                    'video_type': video_type,
                    'brand': brand,
                    'device': '001',
                    'app_name': 'webplayer-abc',
                }
                if video_data.get('accesslevel') == '1':
                    provider_id = site_info['provider_id']
                    software_statement = traverse_obj(data, ('app', 'config', (
                        ('features', 'auth', 'softwareStatement'),
                        ('tvAuth', 'SOFTWARE_STATEMENTS', 'PRODUCTION'),
                    ), {str}, any)) or site_info['software_statement']
                    resource = site_info.get('resource_id') or self._get_mvpd_resource(
                        provider_id, title, video_id, None)
                    auth = self._extract_mvpd_auth(
                        url, video_id, site_info['requestor_id'], resource, software_statement)
                    data.update({
                        'token': auth,
                        'token_type': 'ap',
                        'adobe_requestor_id': provider_id,
                    })
                else:
                    self._initialize_geo_bypass({'countries': ['US']})
                entitlement = self._download_json(
                    'https://prod.gatekeeper.us-abc.symphony.edgedatg.go.com/vp2/ws-secure/entitlement/2020/playmanifest_secure.json',
                    video_id, data=urlencode_postdata(data))
                errors = entitlement.get('errors', {}).get('errors', [])
                if errors:
                    for error in errors:
                        if error.get('code') == 1002:
                            self.raise_geo_restricted(
                                error['message'], countries=['US'])
                    error_message = ', '.join([error['message'] for error in errors])
                    raise ExtractorError(f'{self.IE_NAME} said: {error_message}', expected=True)
                asset_url += '?' + entitlement['entitlement']['uplynkData']['sessionKey']
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    asset_url, video_id, 'mp4', m3u8_id=format_id or 'hls', fatal=False)
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)
            else:
                f = {
                    'format_id': format_id,
                    'url': asset_url,
                    'ext': ext,
                }
                if re.search(r'(?:/mp4/source/|_source\.mp4)', asset_url):
                    f.update({
                        'format_id': (f'{format_id}-' if format_id else '') + 'SOURCE',
                        'quality': 1,
                    })
                else:
                    mobj = re.search(r'/(\d+)x(\d+)/', asset_url)
                    if mobj:
                        height = int(mobj.group(2))
                        f.update({
                            'format_id': join_nonempty(format_id, f'{height}P'),
                            'width': int(mobj.group(1)),
                            'height': height,
                        })
                formats.append(f)

        for cc in video_data.get('closedcaption', {}).get('src', []):
            cc_url = cc.get('value')
            if not cc_url:
                continue
            ext = determine_ext(cc_url)
            if ext == 'xml':
                ext = 'ttml'
            subtitles.setdefault(cc.get('lang'), []).append({
                'url': cc_url,
                'ext': ext,
            })

        thumbnails = []
        for thumbnail in video_data.get('thumbnails', {}).get('thumbnail', []):
            thumbnail_url = thumbnail.get('value')
            if not thumbnail_url:
                continue
            thumbnails.append({
                'url': thumbnail_url,
                'width': int_or_none(thumbnail.get('width')),
                'height': int_or_none(thumbnail.get('height')),
            })

        return {
            'id': video_id,
            'title': title,
            'description': video_data.get('longdescription') or video_data.get('description'),
            'duration': int_or_none(video_data.get('duration', {}).get('value'), 1000),
            'age_limit': parse_age_limit(video_data.get('tvrating', {}).get('rating')),
            'episode_number': int_or_none(video_data.get('episodenumber')),
            'series': video_data.get('show', {}).get('title'),
            'season_number': int_or_none(video_data.get('season', {}).get('num')),
            'thumbnails': thumbnails,
            'formats': formats,
            'subtitles': subtitles,
            'timestamp': unified_timestamp(traverse_obj(video_data, ('airdates', 'airdate', 0))),
        }