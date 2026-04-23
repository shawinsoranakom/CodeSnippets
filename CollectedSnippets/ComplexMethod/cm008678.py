def _real_extract(self, url):
        display_id, community_id, channel_id, sort_by = self._match_valid_url(url).group('id', 'community', 'channel', 'sort')
        channel_id, sort_by = channel_id or 'featured', sort_by or 'new'

        community_data = self._call_api(
            f'web/communities/view/{community_id}', display_id,
            note='Downloading community info', errnote='Unable to download community info')['community']
        channel_data = traverse_obj(self._call_api(
            f'web/communities/view-channel/{community_id}/{channel_id}', display_id,
            note='Downloading channel info', errnote='Unable to download channel info', fatal=False), 'channel') or {}

        title = f'{community_data.get("name") or community_id} - {channel_data.get("display_title") or channel_id}'
        description = self._parse_content_as_text(
            self._parse_json(community_data.get('description_content') or '{}', display_id, fatal=False) or {})
        return self.playlist_result(
            self._entries(
                f'web/posts/fetch/community/{community_id}?channels[]={sort_by}&channels[]={channel_id}',
                display_id, 'Downloading community posts', 'Unable to download community posts'),
            f'{community_id}/{channel_id}', title, description)