def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        category = mobj.group('category')
        video_id = mobj.group('id')

        entries = []

        data = self._download_json(
            'https://raw.githubusercontent.com/pyvideo/data/master/%s/videos/%s.json'
            % (category, video_id), video_id, fatal=False)

        if data:
            for video in data['videos']:
                video_url = video.get('url')
                if video_url:
                    if video.get('type') == 'youtube':
                        entries.append(self.url_result(video_url, 'Youtube'))
                    else:
                        entries.append({
                            'id': compat_str(data.get('id') or video_id),
                            'url': video_url,
                            'title': data['title'],
                            'description': data.get('description') or data.get('summary'),
                            'thumbnail': data.get('thumbnail_url'),
                            'duration': int_or_none(data.get('duration')),
                        })
        else:
            webpage = self._download_webpage(url, video_id)
            title = self._og_search_title(webpage)
            media_urls = self._search_regex(
                r'(?s)Media URL:(.+?)</li>', webpage, 'media urls')
            for m in re.finditer(
                    r'<a[^>]+href=(["\'])(?P<url>http.+?)\1', media_urls):
                media_url = m.group('url')
                if re.match(r'https?://www\.youtube\.com/watch\?v=.*', media_url):
                    entries.append(self.url_result(media_url, 'Youtube'))
                else:
                    entries.append({
                        'id': video_id,
                        'url': media_url,
                        'title': title,
                    })

        return self.playlist_result(entries, video_id)