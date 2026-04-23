def _extract_nbcu_video(self, url, display_id, old_ie_key=None):
        webpage = self._download_webpage(url, display_id)
        settings = self._search_json(
            r'<script[^>]+data-drupal-selector="drupal-settings-json"[^>]*>',
            webpage, 'settings', display_id)

        query = {}
        tve = extract_attributes(get_element_html_by_class('tve-video-deck-app', webpage) or '')
        if tve:
            account_pid = tve.get('data-mpx-media-account-pid') or tve['data-mpx-account-pid']
            account_id = tve['data-mpx-media-account-id']
            metadata = self._parse_json(
                tve.get('data-normalized-video') or '', display_id, fatal=False, transform_source=unescapeHTML)
            video_id = tve.get('data-guid') or metadata['guid']
            if tve.get('data-entitlement') == 'auth':
                auth = settings['tve_adobe_auth']
                release_pid = tve['data-release-pid']
                resource = self._get_mvpd_resource(
                    tve.get('data-adobe-pass-resource-id') or auth['adobePassResourceId'],
                    tve['data-title'], release_pid, tve.get('data-rating'))
                query['auth'] = self._extract_mvpd_auth(
                    url, release_pid, auth['adobePassRequestorId'],
                    resource, auth['adobePassSoftwareStatement'])
        else:
            ls_playlist = traverse_obj(settings, (
                'ls_playlist', lambda _, v: v['defaultGuid'], any, {require('LS playlist')}))
            video_id = ls_playlist['defaultGuid']
            account_pid = ls_playlist.get('mpxMediaAccountPid') or ls_playlist['mpxAccountPid']
            account_id = ls_playlist['mpxMediaAccountId']
            metadata = traverse_obj(ls_playlist, ('videos', lambda _, v: v['guid'] == video_id, any)) or {}

        tp_path = f'{account_pid}/media/guid/{account_id}/{video_id}'
        formats, subtitles = self._extract_nbcu_formats_and_subtitles(tp_path, video_id, query)
        tp_metadata = self._download_theplatform_metadata(tp_path, video_id, fatal=False)
        parsed_info = self._parse_theplatform_metadata(tp_metadata)
        self._merge_subtitles(parsed_info['subtitles'], target=subtitles)

        return {
            **parsed_info,
            **traverse_obj(metadata, {
                'title': ('title', {str}),
                'description': ('description', {str}),
                'duration': ('durationInSeconds', {int_or_none}),
                'timestamp': ('airDate', {parse_iso8601}),
                'thumbnail': ('thumbnailUrl', {url_or_none}),
                'season_number': ('seasonNumber', {int_or_none}),
                'episode_number': ('episodeNumber', {int_or_none}),
                'episode': ('episodeTitle', {str}),
                'series': ('show', {str}),
            }),
            'id': video_id,
            'display_id': display_id,
            'formats': formats,
            'subtitles': subtitles,
            '_old_archive_ids': [make_archive_id(old_ie_key, video_id)] if old_ie_key else None,
        }