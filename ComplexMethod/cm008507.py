def _real_extract(self, url):
        match = self._match_valid_url(url).groupdict()
        video_type, video_id, display_id = match['type'], match['id'], match['display_id']

        url_api_version = 'v2' if video_type == 'missed-event' else 'v1'
        appier_id = '23984824_' + str(random.randint(0, 10000000000))  # Based on the webpage's uuidRandom generator
        video_json = self._call_api(
            f'https://api.rctiplus.com/api/{url_api_version}/{video_type}/{video_id}/url?appierid={appier_id}', display_id, 'Downloading video URL JSON')[0]
        video_url = video_json['url']

        is_upcoming = try_get(video_json, lambda x: x['current_date'] < x['live_at'])
        if is_upcoming is None:
            is_upcoming = try_get(video_json, lambda x: x['current_date'] < x['start_date'])
        if is_upcoming:
            self.raise_no_formats(
                'This event will start at {}.'.format(video_json['live_label']) if video_json.get('live_label') else 'This event has not started yet.', expected=True)
        if 'akamaized' in video_url:
            # For some videos hosted on Akamai's CDN (possibly AES-encrypted ones?), a session needs to at least be made via Conviva's API
            conviva_json_data = {
                **self._CONVIVA_JSON_TEMPLATE,
                'url': video_url,
                'sst': int(time.time()),
            }
            conviva_json_res = self._download_json(
                'https://ff84ae928c3b33064b76dec08f12500465e59a6f.cws.conviva.com/0/wsg', display_id,
                'Creating Conviva session', 'Failed to create Conviva session',
                fatal=False, data=json.dumps(conviva_json_data).encode())
            if conviva_json_res and conviva_json_res.get('err') != 'ok':
                self.report_warning('Conviva said: {}'.format(str(conviva_json_res.get('err'))))

        video_meta, meta_paths = self._call_api(
            f'https://api.rctiplus.com/api/v1/{video_type}/{video_id}', display_id, 'Downloading video metadata')

        thumbnails, image_path = [], meta_paths.get('image_path', 'https://rstatic.akamaized.net/media/')
        if video_meta.get('portrait_image'):
            thumbnails.append({
                'id': 'portrait_image',
                'url': '{}{}{}'.format(image_path, 2000, video_meta['portrait_image']),  # 2000px seems to be the highest resolution that can be given
            })
        if video_meta.get('landscape_image'):
            thumbnails.append({
                'id': 'landscape_image',
                'url': '{}{}{}'.format(image_path, 2000, video_meta['landscape_image']),
            })
        try:
            formats = self._extract_m3u8_formats(video_url, display_id, 'mp4', headers={'Referer': 'https://www.rctiplus.com/'})
        except ExtractorError as e:
            if isinstance(e.cause, HTTPError) and e.cause.status == 403:
                self.raise_geo_restricted(countries=['ID'], metadata_available=True)
            else:
                raise e
        for f in formats:
            if 'akamaized' in f['url'] or 'cloudfront' in f['url']:
                f.setdefault('http_headers', {})['Referer'] = 'https://www.rctiplus.com/'  # Referer header is required for akamai/cloudfront CDNs

        return {
            'id': video_meta.get('product_id') or video_json.get('product_id'),
            'title': dict_get(video_meta, ('title', 'name')) or dict_get(video_json, ('content_name', 'assets_name')),
            'display_id': display_id,
            'description': video_meta.get('summary'),
            'timestamp': video_meta.get('release_date') or video_json.get('start_date'),
            'duration': video_meta.get('duration'),
            'categories': [video_meta['genre']] if video_meta.get('genre') else None,
            'average_rating': video_meta.get('star_rating'),
            'series': video_meta.get('program_title') or video_json.get('program_title'),
            'season_number': video_meta.get('season'),
            'episode_number': video_meta.get('episode'),
            'channel': video_json.get('tv_name'),
            'channel_id': video_json.get('tv_id'),
            'formats': formats,
            'thumbnails': thumbnails,
            'is_live': video_type == 'live-event' and not is_upcoming,
            'was_live': video_type == 'missed-event',
            'live_status': 'is_upcoming' if is_upcoming else None,
            'release_timestamp': video_json.get('live_at'),
        }