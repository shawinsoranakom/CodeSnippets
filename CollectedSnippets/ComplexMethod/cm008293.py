def _extract_from_api(self, program_id, episode_id, asset_id):
        auth_token = self._fetch_auth_token()
        if not auth_token:
            self._report_fallback_warning('auth token', episode_id)
            return None

        episode_data = traverse_obj(self._download_json(
            f'https://www.rtp.pt/play/api/1/get-episode/{program_id[1:]}/{episode_id[1:]}',
            asset_id or episode_id, query={'include_assets': 'true', 'include_webparams': 'true'},
            headers={
                'Accept': '*/*',
                'Authorization': f'Bearer {auth_token}',
                'User-Agent': self._USER_AGENT,
            }, fatal=False), 'result', {dict})
        if not episode_data:
            self._report_fallback_warning('episode data', episode_id)
            return None

        episode_info = {
            'id': episode_id,  # playlist id
            'episode_id': episode_id,
            'series_id': program_id,
            **traverse_obj(episode_data, ('episode', {
                'title': (('episode_title', 'program_title'), {str}, filter, any),
                'alt_title': ('episode_subtitle', {str}, filter),
                'description': (('episode_description', 'episode_summary'), {str}, filter, any),
                'timestamp': ('episode_air_date', {parse_iso8601(delimiter=' ')}),
                'modified_timestamp': ('episode_lastchanged', {parse_iso8601(delimiter=' ')}),
                'duration': ('episode_duration_complete', {parse_duration}),  # playlist duration
                'episode': ('episode_title', {str}, filter),
                'episode_number': ('episode_number', {int_or_none}),
                'season': ('program_season', {str}, filter),
                'series': ('program_title', {str}, filter),
            })),
        }

        assets = traverse_obj(episode_data, ('assets', lambda _, v: v['asset_id']))
        if not assets:
            self._report_fallback_warning('asset IDs', episode_id)
            return None

        if asset_id:
            asset_data = traverse_obj(assets, (lambda _, v: v['asset_id'] == asset_id, any))
            if not asset_data:
                self._report_fallback_warning(f'asset {asset_id}', episode_id)
                return None
            return self._extract_asset(asset_data, episode_id, episode_info)

        asset_data = assets[0]

        if self._yes_playlist(
            len(assets) > 1 and episode_id, asset_data['asset_id'],
            playlist_label='multi-part episode', video_label='individual part',
        ):
            return self.playlist_result(
                self._entries(assets, episode_id, episode_info), **episode_info)

        # Pass archive_compat=True so we return _old_archive_ids for URLs without an asset_id
        return self._extract_asset(asset_data, episode_id, episode_info, archive_compat=True)