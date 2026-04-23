def _real_extract(self, url, smuggled_data):
        item_id = self._match_id(url)
        url = urllib.parse.urlunparse(
            urllib.parse.urlparse(url)._replace(netloc='www.youtube.com'))
        compat_opts = self.get_param('compat_opts', [])

        mobj = self._get_url_mobj(url)
        pre, tab, post, is_channel = mobj['pre'], mobj['tab'], mobj['post'], not mobj['not_channel']
        if is_channel and smuggled_data.get('is_music_url'):
            if item_id[:2] == 'VL':  # Youtube music VL channels have an equivalent playlist
                return self.url_result(
                    f'https://music.youtube.com/playlist?list={item_id[2:]}', YoutubeTabIE, item_id[2:])
            elif item_id[:2] == 'MP':  # Resolve albums (/[channel/browse]/MP...) to their equivalent playlist
                mdata = self._extract_tab_endpoint(
                    f'https://music.youtube.com/browse/{item_id}', item_id, default_client='web_music')
                murl = traverse_obj(mdata, ('microformat', 'microformatDataRenderer', 'urlCanonical'),
                                    get_all=False, expected_type=str)
                if not murl:
                    raise ExtractorError('Failed to resolve album to playlist')
                return self.url_result(murl, YoutubeTabIE)
            elif mobj['channel_type'] == 'browse':  # Youtube music /browse/ should be changed to /channel/
                return self.url_result(
                    f'https://music.youtube.com/channel/{item_id}{tab}{post}', YoutubeTabIE, item_id)

        original_tab_id, display_id = tab[1:], f'{item_id}{tab}'
        if is_channel and not tab and 'no-youtube-channel-redirect' not in compat_opts:
            url = f'{pre}/videos{post}'
        if smuggled_data.get('is_music_url'):
            self.report_warning(f'YouTube Music is not directly supported. Redirecting to {url}')

        # Handle both video/playlist URLs
        qs = parse_qs(url)
        video_id, playlist_id = (traverse_obj(qs, (key, 0)) for key in ('v', 'list'))
        if not video_id and mobj['not_channel'].startswith('watch'):
            if not playlist_id:
                # If there is neither video or playlist ids, youtube redirects to home page, which is undesirable
                raise ExtractorError('A video URL was given without video ID', expected=True)
            # Common mistake: https://www.youtube.com/watch?list=playlist_id
            self.report_warning(f'A video URL was given without video ID. Trying to download playlist {playlist_id}')
            return self.url_result(
                f'https://www.youtube.com/playlist?list={playlist_id}', YoutubeTabIE, playlist_id)

        if not self._yes_playlist(playlist_id, video_id):
            return self.url_result(
                f'https://www.youtube.com/watch?v={video_id}', YoutubeIE, video_id)

        data, ytcfg = self._extract_data(url, display_id)

        # YouTube may provide a non-standard redirect to the regional channel
        # See: https://github.com/yt-dlp/yt-dlp/issues/2694
        # https://support.google.com/youtube/answer/2976814#zippy=,conditional-redirects
        redirect_url = traverse_obj(
            data, ('onResponseReceivedActions', ..., 'navigateAction', 'endpoint', 'commandMetadata', 'webCommandMetadata', 'url'), get_all=False)
        if redirect_url and 'no-youtube-channel-redirect' not in compat_opts:
            redirect_url = ''.join((urljoin('https://www.youtube.com', redirect_url), tab, post))
            self.to_screen(f'This playlist is likely not available in your region. Following conditional redirect to {redirect_url}')
            return self.url_result(redirect_url, YoutubeTabIE)

        tabs, extra_tabs = self._extract_tab_renderers(data), []
        if is_channel and tabs and 'no-youtube-channel-redirect' not in compat_opts:
            selected_tab = self._extract_selected_tab(tabs)
            selected_tab_id, selected_tab_name = self._extract_tab_id_and_name(selected_tab, url)  # NB: Name may be translated
            self.write_debug(f'Selected tab: {selected_tab_id!r} ({selected_tab_name}), Requested tab: {original_tab_id!r}')

            # /about is no longer a tab
            if original_tab_id == 'about':
                return self._empty_playlist(item_id, data)

            if not original_tab_id and selected_tab_name:
                self.to_screen('Downloading all uploads of the channel. '
                               'To download only the videos in a specific tab, pass the tab\'s URL')
                if self._has_tab(tabs, 'streams'):
                    extra_tabs.append(''.join((pre, '/streams', post)))
                if self._has_tab(tabs, 'shorts'):
                    extra_tabs.append(''.join((pre, '/shorts', post)))
                # XXX: Members-only tab should also be extracted

                if not extra_tabs and selected_tab_id != 'videos':
                    # Channel does not have streams, shorts or videos tabs
                    if item_id[:2] != 'UC':
                        return self._empty_playlist(item_id, data)

                    # Topic channels don't have /videos. Use the equivalent playlist instead
                    pl_id = f'UU{item_id[2:]}'
                    pl_url = f'https://www.youtube.com/playlist?list={pl_id}'
                    try:
                        data, ytcfg = self._extract_data(pl_url, pl_id, ytcfg=ytcfg, fatal=True, webpage_fatal=True)
                    except ExtractorError:
                        return self._empty_playlist(item_id, data)
                    else:
                        item_id, url = pl_id, pl_url
                        self.to_screen(
                            f'The channel does not have a videos, shorts, or live tab. Redirecting to playlist {pl_id} instead')

                elif extra_tabs and selected_tab_id != 'videos':
                    # When there are shorts/live tabs but not videos tab
                    url, data = f'{pre}{post}', None

            elif (original_tab_id or 'videos') != selected_tab_id:
                if original_tab_id == 'live':
                    # Live tab should have redirected to the video
                    # Except in the case the channel has an actual live tab
                    # Example: https://www.youtube.com/channel/UCEH7P7kyJIkS_gJf93VYbmg/live
                    raise UserNotLive(video_id=item_id)
                elif selected_tab_name:
                    raise ExtractorError(f'This channel does not have a {original_tab_id} tab', expected=True)

                # For channels such as https://www.youtube.com/channel/UCtFRv9O2AHqOZjjynzrv-xg
                url = f'{pre}{post}'

        # YouTube sometimes provides a button to reload playlist with unavailable videos.
        if 'no-youtube-unavailable-videos' not in compat_opts:
            data = self._reload_with_unavailable_videos(display_id, data, ytcfg) or data
        self._extract_and_report_alerts(data, only_once=True)

        tabs, entries = self._extract_tab_renderers(data), []
        if tabs:
            entries = [self._extract_from_tabs(item_id, ytcfg, data, tabs)]
            entries[0].update({
                'extractor_key': YoutubeTabIE.ie_key(),
                'extractor': YoutubeTabIE.IE_NAME,
                'webpage_url': url,
            })
        if self.get_param('playlist_items') == '0':
            entries.extend(self.url_result(u, YoutubeTabIE) for u in extra_tabs)
        else:  # Users expect to get all `video_id`s even with `--flat-playlist`. So don't return `url_result`
            entries.extend(map(self._real_extract, extra_tabs))

        if len(entries) == 1:
            return entries[0]
        elif entries:
            metadata = self._extract_metadata_from_tabs(item_id, data)
            uploads_url = 'the Uploads (UU) playlist URL'
            if try_get(metadata, lambda x: x['channel_id'].startswith('UC')):
                uploads_url = f'https://www.youtube.com/playlist?list=UU{metadata["channel_id"][2:]}'
            self.to_screen(
                'Downloading as multiple playlists, separated by tabs. '
                f'To download as a single playlist instead, pass {uploads_url}')
            return self.playlist_result(entries, item_id, **metadata)

        # Inline playlist
        playlist = traverse_obj(
            data, ('contents', 'twoColumnWatchNextResults', 'playlist', 'playlist'), expected_type=dict)
        if playlist:
            return self._extract_from_playlist(item_id, url, data, playlist, ytcfg)

        video_id = traverse_obj(
            data, ('currentVideoEndpoint', 'watchEndpoint', 'videoId'), expected_type=str) or video_id
        if video_id:
            if tab != '/live':  # live tab is expected to redirect to video
                self.report_warning(f'Unable to recognize playlist. Downloading just video {video_id}')
            return self.url_result(f'https://www.youtube.com/watch?v={video_id}', YoutubeIE, video_id)

        raise ExtractorError('Unable to recognize tab page')