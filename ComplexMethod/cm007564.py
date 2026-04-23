def _real_extract(self, url):
        # determine video id from url
        m = re.match(self._VALID_URL, url)

        document_id = None

        numid = re.search(r'documentId=([0-9]+)', url)
        if numid:
            document_id = video_id = numid.group(1)
        else:
            video_id = m.group('video_id')

        webpage = self._download_webpage(url, video_id)

        ERRORS = (
            ('>Leider liegt eine Störung vor.', 'Video %s is unavailable'),
            ('>Der gewünschte Beitrag ist nicht mehr verfügbar.<',
             'Video %s is no longer available'),
        )

        for pattern, message in ERRORS:
            if pattern in webpage:
                raise ExtractorError(message % video_id, expected=True)

        if re.search(r'[\?&]rss($|[=&])', url):
            doc = compat_etree_fromstring(webpage.encode('utf-8'))
            if doc.tag == 'rss':
                return GenericIE()._extract_rss(url, video_id, doc)

        title = self._og_search_title(webpage, default=None) or self._html_search_regex(
            [r'<h1(?:\s+class="boxTopHeadline")?>(.*?)</h1>',
             r'<meta name="dcterms\.title" content="(.*?)"/>',
             r'<h4 class="headline">(.*?)</h4>',
             r'<title[^>]*>(.*?)</title>'],
            webpage, 'title')
        description = self._og_search_description(webpage, default=None) or self._html_search_meta(
            'dcterms.abstract', webpage, 'description', default=None)
        if description is None:
            description = self._html_search_meta(
                'description', webpage, 'meta description', default=None)
        if description is None:
            description = self._html_search_regex(
                r'<p\s+class="teasertext">(.+?)</p>',
                webpage, 'teaser text', default=None)

        # Thumbnail is sometimes not present.
        # It is in the mobile version, but that seems to use a different URL
        # structure altogether.
        thumbnail = self._og_search_thumbnail(webpage, default=None)

        media_streams = re.findall(r'''(?x)
            mediaCollection\.addMediaStream\([0-9]+,\s*[0-9]+,\s*"[^"]*",\s*
            "([^"]+)"''', webpage)

        if media_streams:
            QUALITIES = qualities(['lo', 'hi', 'hq'])
            formats = []
            for furl in set(media_streams):
                if furl.endswith('.f4m'):
                    fid = 'f4m'
                else:
                    fid_m = re.match(r'.*\.([^.]+)\.[^.]+$', furl)
                    fid = fid_m.group(1) if fid_m else None
                formats.append({
                    'quality': QUALITIES(fid),
                    'format_id': fid,
                    'url': furl,
                })
            self._sort_formats(formats)
            info = {
                'formats': formats,
            }
        else:  # request JSON file
            if not document_id:
                video_id = self._search_regex(
                    r'/play/(?:config|media)/(\d+)', webpage, 'media id')
            info = self._extract_media_info(
                'http://www.ardmediathek.de/play/media/%s' % video_id,
                webpage, video_id)

        info.update({
            'id': video_id,
            'title': self._live_title(title) if info.get('is_live') else title,
            'description': description,
            'thumbnail': thumbnail,
        })

        return info