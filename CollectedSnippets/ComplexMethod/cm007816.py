def _real_extract(self, url):
        lang, playlist_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, playlist_id)

        items = []
        for video in re.finditer(
                r'<a\b[^>]*?href\s*=\s*(?P<q>"|\'|\b)(?P<url>https?://www\.arte\.tv/%s/videos/[\w/-]+)(?P=q)' % lang,
                webpage):
            video = video.group('url')
            if video == url:
                continue
            if any(ie.suitable(video) for ie in (ArteTVIE, ArteTVPlaylistIE, )):
                items.append(video)

        if items:
            title = (self._og_search_title(webpage, default=None)
                     or self._html_search_regex(r'<title\b[^>]*>([^<]+)</title>', default=None))
            title = strip_or_none(title.rsplit('|', 1)[0]) or self._generic_title(url)

            result = self.playlist_from_matches(items, playlist_id=playlist_id, playlist_title=title)
            if result:
                description = self._og_search_description(webpage, default=None)
                if description:
                    result['description'] = description
                return result