def _real_extract(self, url):
        url, country, display_id = re.match(self._VALID_URL, url).groups()
        if not country:
            country = 'us'
        else:
            country = country.split('-')[0]

        item = self._download_json(
            'https://%s.yahoo.com/caas/content/article' % country, display_id,
            'Downloading content JSON metadata', query={
                'url': url
            })['items'][0]['data']['partnerData']

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
                    if not iframe_url:
                        continue
                    entries.append(self.url_result(iframe_url))

            return self.playlist_result(
                entries, item.get('uuid'),
                item.get('title'), item.get('summary'))

        info = self._extract_yahoo_video(item['uuid'], country)
        info['display_id'] = display_id
        return info