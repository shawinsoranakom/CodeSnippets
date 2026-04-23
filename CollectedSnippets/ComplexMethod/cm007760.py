def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage, urlh = self._download_webpage_handle(url, playlist_id)
        parsed_url = compat_urllib_parse_urlparse(urlh.geturl())
        site_name = self._og_search_property('site_name', webpage, fatal=False, default='Česká televize')
        playlist_title = self._og_search_title(webpage, default=None)
        if site_name and playlist_title:
            playlist_title = re.split(r'\s*[—|]\s*%s' % (site_name, ), playlist_title, 1)[0]
        playlist_description = self._og_search_description(webpage, default=None)
        if playlist_description:
            playlist_description = playlist_description.replace('\xa0', ' ')

        type_ = 'IDEC'
        if re.search(r'(^/porady|/zive)/', parsed_url.path):
            next_data = self._search_nextjs_data(webpage, playlist_id)
            if '/zive/' in parsed_url.path:
                idec = traverse_obj(next_data, ('props', 'pageProps', 'data', 'liveBroadcast', 'current', 'idec'), get_all=False)
            else:
                idec = traverse_obj(next_data, ('props', 'pageProps', 'data', ('show', 'mediaMeta'), 'idec'), get_all=False)
                if not idec:
                    idec = traverse_obj(next_data, ('props', 'pageProps', 'data', 'videobonusDetail', 'bonusId'), get_all=False)
                    if idec:
                        type_ = 'bonus'
            if not idec:
                raise ExtractorError('Failed to find IDEC id')
            iframe_hash = self._download_webpage(
                'https://www.ceskatelevize.cz/v-api/iframe-hash/',
                playlist_id, note='Getting IFRAME hash')
            query = {'hash': iframe_hash, 'origin': 'iVysilani', 'autoStart': 'true', type_: idec, }
            webpage = self._download_webpage(
                'https://www.ceskatelevize.cz/ivysilani/embed/iFramePlayer.php',
                playlist_id, note='Downloading player', query=query)

        NOT_AVAILABLE_STRING = 'This content is not available at your territory due to limited copyright.'
        if '%s</p>' % NOT_AVAILABLE_STRING in webpage:
            self.raise_geo_restricted(NOT_AVAILABLE_STRING)
        if any(not_found in webpage for not_found in ('Neplatný parametr pro videopřehrávač', 'IDEC nebyl nalezen', )):
            raise ExtractorError('no video with IDEC available', video_id=idec, expected=True)

        type_ = None
        episode_id = None

        playlist = self._parse_json(
            self._search_regex(
                r'getPlaylistUrl\(\[({.+?})\]', webpage, 'playlist',
                default='{}'), playlist_id)
        if playlist:
            type_ = playlist.get('type')
            episode_id = playlist.get('id')

        if not type_:
            type_ = self._html_search_regex(
                r'getPlaylistUrl\(\[\{"type":"(.+?)","id":".+?"\}\],',
                webpage, 'type')
        if not episode_id:
            episode_id = self._html_search_regex(
                r'getPlaylistUrl\(\[\{"type":".+?","id":"(.+?)"\}\],',
                webpage, 'episode_id')

        data = {
            'playlist[0][type]': type_,
            'playlist[0][id]': episode_id,
            'requestUrl': parsed_url.path,
            'requestSource': 'iVysilani',
        }

        entries = []

        for user_agent in (None, USER_AGENTS['Safari']):
            req = sanitized_Request(
                'https://www.ceskatelevize.cz/ivysilani/ajax/get-client-playlist/',
                data=urlencode_postdata(data))

            req.add_header('Content-type', 'application/x-www-form-urlencoded')
            req.add_header('x-addr', '127.0.0.1')
            req.add_header('X-Requested-With', 'XMLHttpRequest')
            if user_agent:
                req.add_header('User-Agent', user_agent)
            req.add_header('Referer', url)

            playlistpage = self._download_json(req, playlist_id, fatal=False)

            if not playlistpage:
                continue

            playlist_url = playlistpage['url']
            if playlist_url == 'error_region':
                raise ExtractorError(NOT_AVAILABLE_STRING, expected=True)

            req = sanitized_Request(compat_urllib_parse_unquote(playlist_url))
            req.add_header('Referer', url)

            playlist = self._download_json(req, playlist_id, fatal=False)
            if not playlist:
                continue

            playlist = playlist.get('playlist')
            if not isinstance(playlist, list):
                continue

            playlist_len = len(playlist)

            for num, item in enumerate(playlist):
                is_live = item.get('type') == 'LIVE'
                formats = []
                for format_id, stream_url in item.get('streamUrls', {}).items():
                    if 'drmOnly=true' in stream_url:
                        continue
                    if 'playerType=flash' in stream_url:
                        stream_formats = self._extract_m3u8_formats(
                            stream_url, playlist_id, 'mp4', 'm3u8_native',
                            m3u8_id='hls-%s' % format_id, fatal=False)
                    else:
                        stream_formats = self._extract_mpd_formats(
                            stream_url, playlist_id,
                            mpd_id='dash-%s' % format_id, fatal=False)
                    # See https://github.com/ytdl-org/youtube-dl/issues/12119#issuecomment-280037031
                    if format_id == 'audioDescription':
                        for f in stream_formats:
                            f['source_preference'] = -10
                    formats.extend(stream_formats)

                if user_agent and len(entries) == playlist_len:
                    entries[num]['formats'].extend(formats)
                    continue

                item_id = str_or_none(item.get('id') or item['assetId'])
                title = item['title']

                duration = float_or_none(item.get('duration'))
                thumbnail = item.get('previewImageUrl')

                subtitles = {}
                if item.get('type') == 'VOD':
                    subs = item.get('subtitles')
                    if subs:
                        subtitles = self.extract_subtitles(episode_id, subs)

                if playlist_len == 1:
                    final_title = playlist_title or title
                else:
                    final_title = '%s (%s)' % (playlist_title, title)

                entries.append({
                    'id': item_id,
                    'title': final_title,
                    'description': playlist_description if playlist_len == 1 else None,
                    'thumbnail': thumbnail,
                    'duration': duration,
                    'formats': formats,
                    'subtitles': subtitles,
                    'is_live': is_live,
                })

        for e in entries:
            self._sort_formats(e['formats'])

        if len(entries) == 1:
            return entries[0]
        return self.playlist_result(entries, playlist_id, playlist_title, playlist_description)