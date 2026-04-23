def _real_extract(self, url):
        display_id = self._match_id(url)
        webpage = urllib.parse.unquote(self._download_webpage(url, display_id))

        def create_entry(provider_video_id, provider_video_type, title=None, description=None):
            video_url = {
                'youtube': '%s',
                'volume': 'http://volume.vox-cdn.com/embed/%s',
            }[provider_video_type] % provider_video_id
            return {
                '_type': 'url_transparent',
                'url': video_url,
                'title': title or self._og_search_title(webpage),
                'description': description or self._og_search_description(webpage),
            }

        entries = []
        entries_data = self._search_regex([
            r'Chorus\.VideoContext\.addVideo\((\[{.+}\])\);',
            r'var\s+entry\s*=\s*({.+});',
            r'SBN\.VideoLinkset\.entryGroup\(\s*(\[.+\])',
        ], webpage, 'video data', default=None)
        if entries_data:
            entries_data = self._parse_json(entries_data, display_id)
            if isinstance(entries_data, dict):
                entries_data = [entries_data]
            for video_data in entries_data:
                provider_video_id = video_data.get('provider_video_id')
                provider_video_type = video_data.get('provider_video_type')
                if provider_video_id and provider_video_type:
                    entries.append(create_entry(
                        provider_video_id, provider_video_type,
                        video_data.get('title'), video_data.get('description')))

        volume_uuid = self._search_regex(
            r'data-volume-uuid="([^"]+)"', webpage, 'volume uuid', default=None)
        if volume_uuid:
            entries.append(create_entry(volume_uuid, 'volume'))

        if len(entries) == 1:
            return entries[0]
        else:
            return self.playlist_result(entries, display_id, self._og_search_title(webpage), self._og_search_description(webpage))