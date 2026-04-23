def _real_extract(self, url):
        m = re.match(self._VALID_URL, url)
        fileID = m.group('fileID')
        if fileID:
            videourl = url
            playlist_id = fileID
        else:
            gameID = m.group('gameID')
            playlist_id = gameID
            videourl = self._VIDEO_PAGE_TEMPLATE % playlist_id

        self._set_cookie('steampowered.com', 'mature_content', '1')

        webpage = self._download_webpage(videourl, playlist_id)

        if re.search('<h2>Please enter your birth date to continue:</h2>', webpage) is not None:
            videourl = self._AGECHECK_TEMPLATE % playlist_id
            self.report_age_confirmation()
            webpage = self._download_webpage(videourl, playlist_id)

        flash_vars = self._parse_json(self._search_regex(
            r'(?s)rgMovieFlashvars\s*=\s*({.+?});', webpage,
            'flash vars'), playlist_id, js_to_json)

        playlist_title = None
        entries = []
        if fileID:
            playlist_title = get_element_by_class('workshopItemTitle', webpage)
            for movie in flash_vars.values():
                if not movie:
                    continue
                youtube_id = movie.get('YOUTUBE_VIDEO_ID')
                if not youtube_id:
                    continue
                entries.append({
                    '_type': 'url',
                    'url': youtube_id,
                    'ie_key': 'Youtube',
                })
        else:
            playlist_title = get_element_by_class('apphub_AppName', webpage)
            for movie_id, movie in flash_vars.items():
                if not movie:
                    continue
                video_id = self._search_regex(r'movie_(\d+)', movie_id, 'video id', fatal=False)
                title = movie.get('MOVIE_NAME')
                if not title or not video_id:
                    continue
                entry = {
                    'id': video_id,
                    'title': title.replace('+', ' '),
                }
                formats = []
                flv_url = movie.get('FILENAME')
                if flv_url:
                    formats.append({
                        'format_id': 'flv',
                        'url': flv_url,
                    })
                highlight_element = self._search_regex(
                    r'(<div[^>]+id="highlight_movie_%s"[^>]+>)' % video_id,
                    webpage, 'highlight element', fatal=False)
                if highlight_element:
                    highlight_attribs = extract_attributes(highlight_element)
                    if highlight_attribs:
                        entry['thumbnail'] = highlight_attribs.get('data-poster')
                        for quality in ('', '-hd'):
                            for ext in ('webm', 'mp4'):
                                video_url = highlight_attribs.get('data-%s%s-source' % (ext, quality))
                                if video_url:
                                    formats.append({
                                        'format_id': ext + quality,
                                        'url': video_url,
                                    })
                if not formats:
                    continue
                entry['formats'] = formats
                entries.append(entry)
        if not entries:
            raise ExtractorError('Could not find any videos')

        return self.playlist_result(entries, playlist_id, playlist_title)