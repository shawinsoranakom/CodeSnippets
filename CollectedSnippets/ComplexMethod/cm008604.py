def _real_extract(self, url):
        url, country, display_id = self._match_valid_url(url).groups()
        if not country:
            country = 'us'
        else:
            country = country.split('-')[0]

        items = self._download_json(
            f'https://{country}.yahoo.com/caas/content/article', display_id,
            'Downloading content JSON metadata', query={
                'url': url,
            })['items'][0]

        item = items['data']['partnerData']
        if item.get('type') != 'video':
            entries = []

            cover = item.get('cover') or {}
            if cover.get('type') == 'yvideo':
                cover_url = cover.get('url')
                if cover_url:
                    entries.append(self.url_result(
                        cover_url, 'Yahoo', cover.get('uuid')))

            for e in (item.get('body') or []):
                if e.get('type') == 'videoIframe':
                    iframe_url = e.get('url')
                    if iframe_url:
                        entries.append(self.url_result(iframe_url))

            if item.get('type') == 'storywithleadvideo':
                iframe_url = try_get(item, lambda x: x['meta']['player']['url'])
                if iframe_url:
                    entries.append(self.url_result(iframe_url))
                else:
                    self.report_warning("Yahoo didn't provide an iframe url for this storywithleadvideo")

            if items.get('markup'):
                entries.extend(
                    self.url_result(yt_url) for yt_url in YoutubeIE._extract_embed_urls(url, items['markup']))

            return self.playlist_result(
                entries, item.get('uuid'),
                item.get('title'), item.get('summary'))

        info = self._extract_yahoo_video(item['uuid'], country)
        info['display_id'] = display_id
        return info