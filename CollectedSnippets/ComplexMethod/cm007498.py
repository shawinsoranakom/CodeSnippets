def _real_extract(self, url):
        video_id = self._match_id(url)
        content = self._download_json(
            'https://tv.naver.com/api/json/v/' + video_id,
            video_id, headers=self.geo_verification_headers())
        player_info_json = content.get('playerInfoJson') or {}
        current_clip = player_info_json.get('currentClip') or {}

        vid = current_clip.get('videoId')
        in_key = current_clip.get('inKey')

        if not vid or not in_key:
            player_auth = try_get(player_info_json, lambda x: x['playerOption']['auth'])
            if player_auth == 'notCountry':
                self.raise_geo_restricted(countries=['KR'])
            elif player_auth == 'notLogin':
                self.raise_login_required()
            raise ExtractorError('couldn\'t extract vid and key')
        info = self._extract_video_info(video_id, vid, in_key)
        info.update({
            'description': clean_html(current_clip.get('description')),
            'timestamp': int_or_none(current_clip.get('firstExposureTime'), 1000),
            'duration': parse_duration(current_clip.get('displayPlayTime')),
            'like_count': int_or_none(current_clip.get('recommendPoint')),
            'age_limit': 19 if current_clip.get('adult') else None,
        })
        return info