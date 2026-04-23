def _real_extract(self, url):
        video_id, display_id = self._match_valid_url(url).group('id', 'display_id')
        access_token_request = self._download_json(
            'https://launchapi.zee5.com/launch?platform_name=web_app',
            video_id, note='Downloading access token')['platform_token']
        data = {
            'x-access-token': access_token_request['token'],
        }
        if self._USER_TOKEN:
            data['Authorization'] = f'bearer {self._USER_TOKEN}'
        else:
            data['X-Z5-Guest-Token'] = self._DEVICE_ID

        json_data = self._download_json(
            'https://spapi.zee5.com/singlePlayback/getDetails/secure', video_id, query={
                'content_id': video_id,
                'device_id': self._DEVICE_ID,
                'platform_name': 'desktop_web',
                'country': self._USER_COUNTRY or self.get_param('geo_bypass_country') or 'IN',
                'check_parental_control': False,
            }, headers={'content-type': 'application/json'}, data=json.dumps(data).encode())
        asset_data = json_data['assetDetails']
        show_data = json_data.get('showDetails', {})
        if 'premium' in asset_data['business_type']:
            raise ExtractorError('Premium content is DRM protected.', expected=True)
        if not asset_data.get('hls_url'):
            self.raise_login_required(self._LOGIN_HINT, metadata_available=True, method=None)
        formats, m3u8_subs = self._extract_m3u8_formats_and_subtitles(asset_data['hls_url'], video_id, 'mp4', fatal=False)

        subtitles = {}
        for sub in asset_data.get('subtitle_url', []):
            sub_url = sub.get('url')
            if not sub_url:
                continue
            subtitles.setdefault(sub.get('language', 'en'), []).append({
                'url': self._proto_relative_url(sub_url),
            })
        subtitles = self._merge_subtitles(subtitles, m3u8_subs)
        return {
            'id': video_id,
            'display_id': display_id,
            'title': asset_data['title'],
            'formats': formats,
            'subtitles': subtitles,
            'duration': int_or_none(asset_data.get('duration')),
            'description': str_or_none(asset_data.get('description')),
            'alt_title': str_or_none(asset_data.get('original_title')),
            'uploader': str_or_none(asset_data.get('content_owner')),
            'age_limit': parse_age_limit(asset_data.get('age_rating')),
            'release_date': unified_strdate(asset_data.get('release_date')),
            'timestamp': unified_timestamp(asset_data.get('release_date')),
            'thumbnail': url_or_none(asset_data.get('image_url')),
            'series': str_or_none(asset_data.get('tvshow_name')),
            'season': try_get(show_data, lambda x: x['seasons']['title'], str),
            'season_number': int_or_none(try_get(show_data, lambda x: x['seasons'][0]['orderid'])),
            'episode_number': int_or_none(try_get(asset_data, lambda x: x['orderid'])),
            'tags': try_get(asset_data, lambda x: x['tags'], list),
        }