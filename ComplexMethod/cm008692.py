def _rich_entries(self, rich_grid_renderer):
        if lockup_view_model := traverse_obj(rich_grid_renderer, ('content', 'lockupViewModel', {dict})):
            if entry := self._extract_lockup_view_model(lockup_view_model):
                yield entry
            return
        renderer = traverse_obj(
            rich_grid_renderer,
            ('content', ('videoRenderer', 'reelItemRenderer', 'playlistRenderer', 'shortsLockupViewModel'), any)) or {}
        video_id = renderer.get('videoId')
        if video_id:
            yield self._extract_video(renderer)
            return
        playlist_id = renderer.get('playlistId')
        if playlist_id:
            yield self.url_result(
                f'https://www.youtube.com/playlist?list={playlist_id}',
                ie=YoutubeTabIE.ie_key(), video_id=playlist_id,
                video_title=self._get_text(renderer, 'title'))
            return
        # shortsLockupViewModel extraction
        entity_id = renderer.get('entityId')
        if entity_id:
            video_id = traverse_obj(renderer, ('onTap', 'innertubeCommand', 'reelWatchEndpoint', 'videoId', {str}))
            if not video_id:
                return
            yield self.url_result(
                f'https://www.youtube.com/shorts/{video_id}',
                ie=YoutubeIE, video_id=video_id,
                **traverse_obj(renderer, {
                    'title': ((
                        ('overlayMetadata', 'primaryText', 'content', {str}),
                        ('accessibilityText', {lambda x: re.fullmatch(r'(.+), (?:[\d,.]+(?:[KM]| million)?|No) views? - play Short', x)}, 1)), any),
                    'view_count': ('overlayMetadata', 'secondaryText', 'content', {parse_count}),
                }),
                thumbnails=self._extract_thumbnails(
                    renderer, ('thumbnailViewModel', 'thumbnailViewModel', 'image'), final_key='sources'))
            return