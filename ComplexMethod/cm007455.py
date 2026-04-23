def _real_extract(self, url):
        item_id = self._match_id(url)

        info_dict = {}
        formats = []

        ENDPOINTS = (
            'https://feeds.rasset.ie/rteavgen/player/playlist?type=iptv&format=json&showId=',
            'http://www.rte.ie/rteavgen/getplaylist/?type=web&format=json&id=',
        )

        for num, ep_url in enumerate(ENDPOINTS, start=1):
            try:
                data = self._download_json(ep_url + item_id, item_id)
            except ExtractorError as ee:
                if num < len(ENDPOINTS) or formats:
                    continue
                if isinstance(ee.cause, compat_HTTPError) and ee.cause.code == 404:
                    error_info = self._parse_json(ee.cause.read().decode(), item_id, fatal=False)
                    if error_info:
                        raise ExtractorError(
                            '%s said: %s' % (self.IE_NAME, error_info['message']),
                            expected=True)
                raise

            # NB the string values in the JSON are stored using XML escaping(!)
            show = try_get(data, lambda x: x['shows'][0], dict)
            if not show:
                continue

            if not info_dict:
                title = unescapeHTML(show['title'])
                description = unescapeHTML(show.get('description'))
                thumbnail = show.get('thumbnail')
                duration = float_or_none(show.get('duration'), 1000)
                timestamp = parse_iso8601(show.get('published'))
                info_dict = {
                    'id': item_id,
                    'title': title,
                    'description': description,
                    'thumbnail': thumbnail,
                    'timestamp': timestamp,
                    'duration': duration,
                }

            mg = try_get(show, lambda x: x['media:group'][0], dict)
            if not mg:
                continue

            if mg.get('url'):
                m = re.match(r'(?P<url>rtmpe?://[^/]+)/(?P<app>.+)/(?P<playpath>mp4:.*)', mg['url'])
                if m:
                    m = m.groupdict()
                    formats.append({
                        'url': m['url'] + '/' + m['app'],
                        'app': m['app'],
                        'play_path': m['playpath'],
                        'player_url': url,
                        'ext': 'flv',
                        'format_id': 'rtmp',
                    })

            if mg.get('hls_server') and mg.get('hls_url'):
                formats.extend(self._extract_m3u8_formats(
                    mg['hls_server'] + mg['hls_url'], item_id, 'mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))

            if mg.get('hds_server') and mg.get('hds_url'):
                formats.extend(self._extract_f4m_formats(
                    mg['hds_server'] + mg['hds_url'], item_id,
                    f4m_id='hds', fatal=False))

            mg_rte_server = str_or_none(mg.get('rte:server'))
            mg_url = str_or_none(mg.get('url'))
            if mg_rte_server and mg_url:
                hds_url = url_or_none(mg_rte_server + mg_url)
                if hds_url:
                    formats.extend(self._extract_f4m_formats(
                        hds_url, item_id, f4m_id='hds', fatal=False))

        self._sort_formats(formats)

        info_dict['formats'] = formats
        return info_dict