def _real_extract(self, url):
        video_id = self._match_id(url)
        temp = video_id.split('-')
        series_id = temp[0]
        season_id = temp[1]
        episode_id = temp[2]

        webpage_url = f'https://w.duboku.io/vodplay/{video_id}.html'
        webpage_html = self._download_webpage(webpage_url, video_id)

        # extract video url

        player_data = self._search_regex(
            self._PLAYER_DATA_PATTERN, webpage_html, 'player_data')
        player_data = self._parse_json(player_data, video_id, js_to_json)

        # extract title

        temp = get_elements_by_class('title', webpage_html)
        series_title = None
        title = None
        for html in temp:
            mobj = re.search(r'<a\s+.*>(.*)</a>', html)
            if mobj:
                href = extract_attributes(mobj.group(0)).get('href')
                if href:
                    mobj1 = re.search(r'/(\d+)\.html', href)
                    if mobj1 and mobj1.group(1) == series_id:
                        series_title = clean_html(mobj.group(0))
                        series_title = re.sub(r'[\s\r\n\t]+', ' ', series_title)
                        title = clean_html(html)
                        title = re.sub(r'[\s\r\n\t]+', ' ', title)
                        break

        data_url = player_data.get('url')
        if not data_url:
            raise ExtractorError('Cannot find url in player_data')
        player_encrypt = player_data.get('encrypt')
        if player_encrypt == 1:
            data_url = urllib.parse.unquote(data_url)
        elif player_encrypt == 2:
            data_url = urllib.parse.unquote(base64.b64decode(data_url).decode('ascii'))

        # if it is an embedded iframe, maybe it's an external source
        headers = {'Referer': webpage_url}
        if player_data.get('from') == 'iframe':
            # use _type url_transparent to retain the meaningful details
            # of the video.
            return {
                '_type': 'url_transparent',
                'url': smuggle_url(data_url, {'referer': webpage_url}),
                'id': video_id,
                'title': title,
                'series': series_title,
                'season_number': int_or_none(season_id),
                'season_id': season_id,
                'episode_number': int_or_none(episode_id),
                'episode_id': episode_id,
            }

        formats = self._extract_m3u8_formats(data_url, video_id, 'mp4', headers=headers)

        return {
            'id': video_id,
            'title': title,
            'series': series_title,
            'season_number': int_or_none(season_id),
            'season_id': season_id,
            'episode_number': int_or_none(episode_id),
            'episode_id': episode_id,
            'formats': formats,
            'http_headers': headers,
        }