def _rich_grid_entries(self, contents):
        for content in traverse_obj(
                contents, (Ellipsis, 'richItemRenderer', 'content'),
                expected_type=dict):
            video_renderer = traverse_obj(
                content, 'videoRenderer', 'reelItemRenderer',
                expected_type=dict)
            if video_renderer:
                entry = self._video_entry(video_renderer)
                if entry:
                    yield entry
            # shorts item
            shorts_lockup_view_model = content.get('shortsLockupViewModel')
            if shorts_lockup_view_model:
                entry = self._extract_shorts_lockup_view_model(shorts_lockup_view_model)
                if entry:
                    yield entry
            # playlist
            renderer = traverse_obj(
                content, 'playlistRenderer', expected_type=dict) or {}
            title = self._get_text(renderer, 'title')
            playlist_id = renderer.get('playlistId')
            if playlist_id:
                yield self.url_result(
                    'https://www.youtube.com/playlist?list=%s' % playlist_id,
                    ie=YoutubeTabIE.ie_key(), video_id=playlist_id,
                    video_title=title)