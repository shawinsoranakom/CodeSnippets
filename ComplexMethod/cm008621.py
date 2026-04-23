def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        title = self._og_search_title(webpage) or self._html_extract_title(webpage)
        timestamp = unified_timestamp(
            self._og_search_property('published_time', webpage, default=None)
            or self._html_search_meta('article:published_time', webpage))
        plugin_data = re.findall(r'\$bp\("(?:Brid|TargetVideo)_\d+",\s(.+)\);', webpage)
        entries = []
        if plugin_data:
            site_id = self._html_search_regex(r'site:(\d+)', webpage, 'site id', default=None)
            if site_id is None:
                site_id = self._search_regex(
                    r'partners/(\d+)', self._html_search_meta('contentUrl', webpage, fatal=True), 'site ID')
            for video_data in plugin_data:
                video_id = self._parse_json(video_data, title)['video']
                entries.append({
                    'id': video_id,
                    'title': title,
                    'timestamp': timestamp,
                    'thumbnail': self._html_search_meta('thumbnailURL', webpage),
                    'formats': self._extract_m3u8_formats(
                        f'https://cdn-uc.brid.tv/live/partners/{site_id}/streaming/{video_id}/{video_id}.m3u8',
                        video_id, fatal=False),
                })
        else:
            # Old player still present in older articles
            videos = re.findall(r'(?m)(<video[^>]+>)', webpage)
            for video in videos:
                video_data = extract_attributes(video)
                entries.append({
                    '_type': 'url_transparent',
                    'url': video_data.get('data-url'),
                    'id': video_data.get('id'),
                    'title': title,
                    'thumbnail': traverse_obj(video_data, (('data-thumbnail', 'data-default_thumbnail'), {url_or_none}, any)),
                    'timestamp': timestamp,
                    'ie_key': 'N1InfoAsset',
                })

        embedded_videos = re.findall(r'(<iframe[^>]+>)', webpage)
        for embedded_video in embedded_videos:
            video_data = extract_attributes(embedded_video)
            url = video_data.get('src') or ''
            hostname = urllib.parse.urlparse(url).hostname
            if hostname == 'www.youtube.com':
                entries.append(self.url_result(url, ie='Youtube'))
            elif hostname == 'www.redditmedia.com':
                entries.append(self.url_result(url, ie='Reddit'))
            elif hostname == 'www.facebook.com' and 'plugins/video' in url:
                entries.append(self.url_result(url, ie='FacebookPluginsVideo'))

        return {
            '_type': 'playlist',
            'id': video_id,
            'title': title,
            'timestamp': timestamp,
            'entries': entries,
        }