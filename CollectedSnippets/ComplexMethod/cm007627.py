def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        content_item_id = None

        content_item_url = self._html_search_meta(
            ('og:url', 'og:video', 'og:video:secure_url', 'twitter:url',
             'twitter:player', 'jsonlink'), webpage, default=None)
        if content_item_url:
            content_item_id = self._search_regex(
                r'ContentItem-(%s)' % self._UUID_RE, content_item_url,
                'content item id', default=None)

        if not content_item_id:
            content_item_id = self._search_regex(
                r'''(?x)
                    (?:
                        (?:initEdizione|drawMediaRaiTV)\(|
                        <(?:[^>]+\bdata-id|var\s+uniquename)=|
                        <iframe[^>]+\bsrc=
                    )
                    (["\'])
                    (?:(?!\1).)*\bContentItem-(?P<id>%s)
                ''' % self._UUID_RE,
                webpage, 'content item id', default=None, group='id')

        content_item_ids = set()
        if content_item_id:
            content_item_ids.add(content_item_id)
        if video_id not in content_item_ids:
            content_item_ids.add(video_id)

        for content_item_id in content_item_ids:
            try:
                return self._extract_from_content_id(content_item_id, url)
            except GeoRestrictedError:
                raise
            except ExtractorError:
                pass

        relinker_url = self._proto_relative_url(self._search_regex(
            r'''(?x)
                (?:
                    var\s+videoURL|
                    mediaInfo\.mediaUri
                )\s*=\s*
                ([\'"])
                (?P<url>
                    (?:https?:)?
                    //mediapolis(?:vod)?\.rai\.it/relinker/relinkerServlet\.htm\?
                    (?:(?!\1).)*\bcont=(?:(?!\1).)+)\1
            ''',
            webpage, 'relinker URL', group='url'))

        relinker_info = self._extract_relinker_info(
            urljoin(url, relinker_url), video_id)
        self._sort_formats(relinker_info['formats'])

        title = self._search_regex(
            r'var\s+videoTitolo\s*=\s*([\'"])(?P<title>[^\'"]+)\1',
            webpage, 'title', group='title',
            default=None) or self._og_search_title(webpage)

        info = {
            'id': video_id,
            'title': title,
        }

        info.update(relinker_info)

        return info