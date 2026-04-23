def _extract_entries(self, parent_renderer, continuation_list):
        # continuation_list is modified in-place with continuation_list = [continuation_token]
        continuation_list[:] = [None]
        contents = try_get(parent_renderer, lambda x: x['contents'], list) or []
        for content in contents:
            if not isinstance(content, dict):
                continue
            is_renderer = traverse_obj(
                content, 'itemSectionRenderer', 'musicShelfRenderer', 'musicShelfContinuation',
                expected_type=dict)
            if not is_renderer:
                if content.get('richItemRenderer'):
                    for entry in self._rich_entries(content['richItemRenderer']):
                        yield entry
                    continuation_list[0] = self._extract_continuation(parent_renderer)
                elif content.get('reportHistorySectionRenderer'):  # https://www.youtube.com/reporthistory
                    table = traverse_obj(content, ('reportHistorySectionRenderer', 'table', 'tableRenderer'))
                    yield from self._report_history_entries(table)
                    continuation_list[0] = self._extract_continuation(table)
                continue

            isr_contents = try_get(is_renderer, lambda x: x['contents'], list) or []
            for isr_content in isr_contents:
                if not isinstance(isr_content, dict):
                    continue

                known_renderers = {
                    'playlistVideoListRenderer': self._playlist_entries,
                    'gridRenderer': self._grid_entries,
                    'reelShelfRenderer': self._grid_entries,
                    'shelfRenderer': self._shelf_entries,
                    'musicResponsiveListItemRenderer': lambda x: [self._music_reponsive_list_entry(x)],
                    'backstagePostThreadRenderer': self._post_thread_entries,
                    'videoRenderer': lambda x: [self._video_entry(x)],
                    'playlistRenderer': lambda x: self._grid_entries({'items': [{'playlistRenderer': x}]}),
                    'channelRenderer': lambda x: self._grid_entries({'items': [{'channelRenderer': x}]}),
                    'hashtagTileRenderer': lambda x: [self._hashtag_tile_entry(x)],
                    'richGridRenderer': lambda x: self._extract_entries(x, continuation_list),
                    'lockupViewModel': lambda x: [self._extract_lockup_view_model(x)],
                }
                for key, renderer in isr_content.items():
                    if key not in known_renderers:
                        continue
                    for entry in known_renderers[key](renderer):
                        if entry:
                            yield entry
                    continuation_list[0] = self._extract_continuation(renderer)
                    break

            if not continuation_list[0]:
                continuation_list[0] = self._extract_continuation(is_renderer)

        if not continuation_list[0]:
            continuation_list[0] = self._extract_continuation(parent_renderer)