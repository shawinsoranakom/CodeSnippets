def _real_extract(self, url):
        username, slug = self._match_valid_url(url).groups()
        username = urllib.parse.unquote(username)
        if not slug:
            slug = 'uploads'
        else:
            slug = urllib.parse.unquote(slug)
        playlist_id = f'{username}_{slug}'

        is_playlist_type = self._ROOT_TYPE == 'playlist'
        playlist_type = 'items' if is_playlist_type else slug
        list_filter = ''

        has_next_page = True
        entries = []
        while has_next_page:
            playlist = self._call_api(
                self._ROOT_TYPE, '''%s
    %s
    %s(first: 100%s) {
      edges {
        node {
          %s
        }
      }
      pageInfo {
        endCursor
        hasNextPage
      }
    }''' % (self._TITLE_KEY, self._DESCRIPTION_KEY, playlist_type, list_filter, self._NODE_TEMPLATE),  # noqa: UP031
                playlist_id, username, slug if is_playlist_type else None)

            items = playlist.get(playlist_type) or {}
            for edge in items.get('edges', []):
                cloudcast = self._get_cloudcast(edge.get('node') or {})
                cloudcast_url = cloudcast.get('url')
                if not cloudcast_url:
                    continue
                item_slug = try_get(cloudcast, lambda x: x['slug'], str)
                owner_username = try_get(cloudcast, lambda x: x['owner']['username'], str)
                video_id = f'{owner_username}_{item_slug}' if item_slug and owner_username else None
                entries.append(self.url_result(
                    cloudcast_url, MixcloudIE.ie_key(), video_id))

            page_info = items['pageInfo']
            has_next_page = page_info['hasNextPage']
            list_filter = ', after: "{}"'.format(page_info['endCursor'])

        return self.playlist_result(
            entries, playlist_id,
            self._get_playlist_title(playlist[self._TITLE_KEY], slug),
            playlist.get(self._DESCRIPTION_KEY))