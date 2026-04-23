def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = self._download_webpage(url, display_id)
        webpage_json_data = self._search_json(
            r'var\s*BOXCAST_PRELOAD\s*=', webpage, 'broadcast data', display_id,
            transform_source=js_to_json, default={})

        # Ref: https://support.boxcast.com/en/articles/4235158-build-a-custom-viewer-experience-with-boxcast-api
        broadcast_json_data = (
            traverse_obj(webpage_json_data, ('broadcast', 'data'))
            or self._download_json(f'https://api.boxcast.com/broadcasts/{display_id}', display_id))
        view_json_data = (
            traverse_obj(webpage_json_data, ('view', 'data'))
            or self._download_json(f'https://api.boxcast.com/broadcasts/{display_id}/view',
                                   display_id, fatal=False) or {})

        formats, subtitles = [], {}
        if view_json_data.get('status') == 'recorded':
            formats, subtitles = self._extract_m3u8_formats_and_subtitles(
                view_json_data['playlist'], display_id)

        return {
            'id': str(broadcast_json_data['id']),
            'title': (broadcast_json_data.get('name')
                      or self._html_search_meta(['og:title', 'twitter:title'], webpage)),
            'description': (broadcast_json_data.get('description')
                            or self._html_search_meta(['og:description', 'twitter:description'], webpage)
                            or None),
            'thumbnail': (broadcast_json_data.get('preview')
                          or self._html_search_meta(['og:image', 'twitter:image'], webpage)),
            'formats': formats,
            'subtitles': subtitles,
            'release_timestamp': unified_timestamp(broadcast_json_data.get('streamed_at')),
            'uploader': broadcast_json_data.get('account_name'),
            'uploader_id': broadcast_json_data.get('account_id'),
        }