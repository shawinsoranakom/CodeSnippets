def _extract_inline_playlist(self, playlist, playlist_id, data, ytcfg):
        first_id = last_id = response = None
        for page_num in itertools.count(1):
            videos = list(self._playlist_entries(playlist))
            if not videos:
                return
            start = next((i for i, v in enumerate(videos) if v['id'] == last_id), -1) + 1
            if start >= len(videos):
                return
            yield from videos[start:]
            first_id = first_id or videos[0]['id']
            last_id = videos[-1]['id']
            watch_endpoint = try_get(
                playlist, lambda x: x['contents'][-1]['playlistPanelVideoRenderer']['navigationEndpoint']['watchEndpoint'])
            headers = self.generate_api_headers(
                ytcfg=ytcfg, delegated_session_id=self._extract_delegated_session_id(ytcfg, data),
                visitor_data=self._extract_visitor_data(response, data, ytcfg))
            query = {
                'playlistId': playlist_id,
                'videoId': watch_endpoint.get('videoId') or last_id,
                'index': watch_endpoint.get('index') or len(videos),
                'params': watch_endpoint.get('params') or 'OAE%3D',
            }
            response = self._extract_response(
                item_id=f'{playlist_id} page {page_num}',
                query=query, ep='next', headers=headers, ytcfg=ytcfg,
                check_get_keys='contents',
            )
            playlist = try_get(
                response, lambda x: x['contents']['twoColumnWatchNextResults']['playlist']['playlist'], dict)