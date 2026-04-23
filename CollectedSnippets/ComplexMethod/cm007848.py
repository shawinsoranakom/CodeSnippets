def _real_extract(self, url):
        item_id = self._match_id(url)
        url = update_url(url, netloc='www.youtube.com')
        qs = parse_qs(url)

        def qs_get(key, default=None):
            return qs.get(key, [default])[-1]

        # Go around for /feeds/videos.xml?playlist_id={pl_id}
        if item_id == 'feeds' and '/feeds/videos.xml?' in url:
            playlist_id = qs_get('playlist_id')
            if playlist_id:
                return self.url_result(
                    update_url_query('https://www.youtube.com/playlist', {
                        'list': playlist_id,
                    }), ie=self.ie_key(), video_id=playlist_id)

        # Handle both video/playlist URLs
        video_id = qs_get('v')
        playlist_id = qs_get('list')
        if video_id and playlist_id:
            if self._downloader.params.get('noplaylist'):
                self.to_screen('Downloading just video %s because of --no-playlist' % video_id)
                return self.url_result(video_id, ie=YoutubeIE.ie_key(), video_id=video_id)
            self.to_screen('Downloading playlist %s - add --no-playlist to just download video %s' % (playlist_id, video_id))
        webpage = self._download_webpage(url, item_id)
        data = self._extract_yt_initial_data(item_id, webpage)
        tabs = try_get(
            data, lambda x: x['contents']['twoColumnBrowseResultsRenderer']['tabs'], list)
        if tabs:
            return self._extract_from_tabs(item_id, webpage, data, tabs)
        playlist = try_get(
            data, lambda x: x['contents']['twoColumnWatchNextResults']['playlist']['playlist'], dict)
        if playlist:
            return self._extract_from_playlist(item_id, url, data, playlist)
        # Fallback to video extraction if no playlist alike page is recognized.
        # First check for the current video then try the v attribute of URL query.
        video_id = try_get(
            data, lambda x: x['currentVideoEndpoint']['watchEndpoint']['videoId'],
            compat_str) or video_id
        if video_id:
            return self.url_result(video_id, ie=YoutubeIE.ie_key(), video_id=video_id)

        # Capture and output alerts
        self._extract_and_report_alerts(data)

        # Failed to recognize
        raise ExtractorError('Unable to recognize tab page')