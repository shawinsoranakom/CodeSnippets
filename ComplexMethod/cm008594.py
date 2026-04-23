def _get_formats_and_subtitles(self, asset_id, **kwargs):
        bearer_token = self._get_bearer_token(asset_id, **kwargs)
        api_response = self._download_json(
            f'{self._API_URL}/entitlement/{asset_id}/play',
            asset_id, headers={
                'Authorization': f'Bearer {bearer_token}',
                'Accept': 'application/json, text/plain, */*',
            })

        formats, subtitles = [], {}
        for format_data in api_response['formats']:
            if not format_data.get('mediaLocator'):
                continue

            fmts, subs = [], {}
            if format_data.get('format') == 'DASH':
                fmts, subs = self._extract_mpd_formats_and_subtitles(
                    format_data['mediaLocator'], asset_id, fatal=False)
            elif format_data.get('format') == 'SMOOTHSTREAMING':
                fmts, subs = self._extract_ism_formats_and_subtitles(
                    format_data['mediaLocator'], asset_id, fatal=False)
            elif format_data.get('format') == 'HLS':
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    format_data['mediaLocator'], asset_id, fatal=False)

            if format_data.get('drm'):
                for f in fmts:
                    f['has_drm'] = True

            formats.extend(fmts)
            self._merge_subtitles(subs, target=subtitles)

        return formats, subtitles