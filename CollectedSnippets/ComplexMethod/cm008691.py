def _grid_entries(self, grid_renderer):
        for item in grid_renderer['items']:
            if not isinstance(item, dict):
                continue
            if lockup_view_model := traverse_obj(item, ('lockupViewModel', {dict})):
                if entry := self._extract_lockup_view_model(lockup_view_model):
                    yield entry
                continue
            renderer = self._extract_basic_item_renderer(item)
            if not isinstance(renderer, dict):
                continue
            title = self._get_text(renderer, 'title')

            # playlist
            playlist_id = renderer.get('playlistId')
            if playlist_id:
                yield self.url_result(
                    f'https://www.youtube.com/playlist?list={playlist_id}',
                    ie=YoutubeTabIE.ie_key(), video_id=playlist_id,
                    video_title=title)
                continue
            # video
            video_id = renderer.get('videoId')
            if video_id:
                yield self._extract_video(renderer)
                continue
            # channel
            channel_id = renderer.get('channelId')
            if channel_id:
                yield self._extract_channel_renderer(renderer)
                continue
            # generic endpoint URL support
            ep_url = urljoin('https://www.youtube.com/', try_get(
                renderer, lambda x: x['navigationEndpoint']['commandMetadata']['webCommandMetadata']['url'],
                str))
            if ep_url:

                for ie in (YoutubeTabIE, YoutubePlaylistIE, YoutubeIE):
                    if ie.suitable(ep_url):
                        yield self.url_result(
                            ep_url, ie=ie.ie_key(), video_id=ie._match_id(ep_url), video_title=title)
                        break