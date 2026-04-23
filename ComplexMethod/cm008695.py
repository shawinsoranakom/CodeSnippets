def _entries(self, tab, item_id, ytcfg, delegated_session_id, visitor_data):
        continuation_list = [None]
        extract_entries = lambda x: self._extract_entries(x, continuation_list)
        tab_content = try_get(tab, lambda x: x['content'], dict)
        if not tab_content:
            return
        parent_renderer = (
            try_get(tab_content, lambda x: x['sectionListRenderer'], dict)
            or try_get(tab_content, lambda x: x['richGridRenderer'], dict) or {})
        yield from extract_entries(parent_renderer)
        continuation = continuation_list[0]
        seen_continuations = set()
        for page_num in itertools.count(1):
            if not continuation:
                break
            continuation_token = continuation.get('continuation')
            if continuation_token is not None and continuation_token in seen_continuations:
                self.write_debug('Detected YouTube feed looping - assuming end of feed.')
                break
            seen_continuations.add(continuation_token)
            headers = self.generate_api_headers(
                ytcfg=ytcfg, delegated_session_id=delegated_session_id, visitor_data=visitor_data)
            response = self._extract_response(
                item_id=f'{item_id} page {page_num}',
                query=continuation, headers=headers, ytcfg=ytcfg,
                check_get_keys=(
                    'continuationContents', 'onResponseReceivedActions', 'onResponseReceivedEndpoints',
                    # Playlist recommendations may return with no data - ignore
                    ('responseContext', 'serviceTrackingParams', ..., 'params', ..., lambda k, v: k == 'key' and v == 'GetRecommendedMusicPlaylists_rid'),
                ))

            if not response:
                break

            continuation = None
            # Extracting updated visitor data is required to prevent an infinite extraction loop in some cases
            # See: https://github.com/ytdl-org/youtube-dl/issues/28702
            visitor_data = self._extract_visitor_data(response) or visitor_data

            known_renderers = {
                'videoRenderer': (self._grid_entries, 'items'),  # for membership tab
                'gridPlaylistRenderer': (self._grid_entries, 'items'),
                'gridVideoRenderer': (self._grid_entries, 'items'),
                'gridChannelRenderer': (self._grid_entries, 'items'),
                'playlistVideoRenderer': (self._playlist_entries, 'contents'),
                'itemSectionRenderer': (extract_entries, 'contents'),  # for feeds
                'richItemRenderer': (extract_entries, 'contents'),  # for hashtag
                'backstagePostThreadRenderer': (self._post_thread_continuation_entries, 'contents'),
                'reportHistoryTableRowRenderer': (self._report_history_entries, 'rows'),
                'playlistVideoListContinuation': (self._playlist_entries, None),
                'gridContinuation': (self._grid_entries, None),
                'itemSectionContinuation': (self._post_thread_continuation_entries, None),
                'sectionListContinuation': (extract_entries, None),  # for feeds
                'lockupViewModel': (self._grid_entries, 'items'),  # for playlists tab
            }

            continuation_items = traverse_obj(response, (
                ('onResponseReceivedActions', 'onResponseReceivedEndpoints'), ...,
                'appendContinuationItemsAction', 'continuationItems',
            ), 'continuationContents', get_all=False)
            continuation_item = traverse_obj(continuation_items, 0, None, expected_type=dict, default={})

            video_items_renderer = None
            for key in continuation_item:
                if key not in known_renderers:
                    continue
                func, parent_key = known_renderers[key]
                video_items_renderer = {parent_key: continuation_items} if parent_key else continuation_items
                continuation_list = [None]
                yield from func(video_items_renderer)
                continuation = continuation_list[0] or self._extract_continuation(video_items_renderer)

            # In the case only a continuation is returned, try to follow it.
            # We extract this after trying to extract non-continuation items as otherwise this
            # may be prioritized over other continuations.
            # see: https://github.com/yt-dlp/yt-dlp/issues/12933
            continuation = continuation or self._extract_continuation({'contents': [continuation_item]})

            if not continuation and not video_items_renderer:
                break