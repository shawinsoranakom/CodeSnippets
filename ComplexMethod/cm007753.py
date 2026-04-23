def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        if not display_id:
            display_id = video_id

        if video_id.isdigit() and len(video_id) < 11:
            url_pattern = 'http://www.xtube.com/video-watch/-%s'
        else:
            url_pattern = 'http://www.xtube.com/watch.php?v=%s'

        webpage = self._download_webpage(
            url_pattern % video_id, display_id, headers={
                'Cookie': 'age_verified=1; cookiesAccepted=1',
            })

        title, thumbnail, duration, sources, media_definition = [None] * 5

        config = self._parse_json(self._search_regex(
            r'playerConf\s*=\s*({.+?})\s*,\s*(?:\n|loaderConf|playerWrapper)', webpage, 'config',
            default='{}'), video_id, transform_source=js_to_json, fatal=False)
        if config:
            config = config.get('mainRoll')
            if isinstance(config, dict):
                title = config.get('title')
                thumbnail = config.get('poster')
                duration = int_or_none(config.get('duration'))
                sources = config.get('sources') or config.get('format')
                media_definition = config.get('mediaDefinition')

        if not isinstance(sources, dict) and not media_definition:
            sources = self._parse_json(self._search_regex(
                r'(["\'])?sources\1?\s*:\s*(?P<sources>{.+?}),',
                webpage, 'sources', group='sources'), video_id,
                transform_source=js_to_json)

        formats = []
        format_urls = set()

        if isinstance(sources, dict):
            for format_id, format_url in sources.items():
                format_url = url_or_none(format_url)
                if not format_url:
                    continue
                if format_url in format_urls:
                    continue
                format_urls.add(format_url)
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                    'height': int_or_none(format_id),
                })

        if isinstance(media_definition, list):
            for media in media_definition:
                video_url = url_or_none(media.get('videoUrl'))
                if not video_url:
                    continue
                if video_url in format_urls:
                    continue
                format_urls.add(video_url)
                format_id = media.get('format')
                if format_id == 'hls':
                    formats.extend(self._extract_m3u8_formats(
                        video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id='hls', fatal=False))
                elif format_id == 'mp4':
                    height = int_or_none(media.get('quality'))
                    formats.append({
                        'url': video_url,
                        'format_id': '%s-%d' % (format_id, height) if height else format_id,
                        'height': height,
                    })

        self._remove_duplicate_formats(formats)
        self._sort_formats(formats)

        if not title:
            title = self._search_regex(
                (r'<h1>\s*(?P<title>[^<]+?)\s*</h1>', r'videoTitle\s*:\s*(["\'])(?P<title>.+?)\1'),
                webpage, 'title', group='title')
        description = self._og_search_description(
            webpage, default=None) or self._html_search_meta(
            'twitter:description', webpage, default=None) or self._search_regex(
            r'</h1>\s*<p>([^<]+)', webpage, 'description', fatal=False)
        uploader = self._search_regex(
            (r'<input[^>]+name="contentOwnerId"[^>]+value="([^"]+)"',
             r'<span[^>]+class="nickname"[^>]*>([^<]+)'),
            webpage, 'uploader', fatal=False)
        if not duration:
            duration = parse_duration(self._search_regex(
                r'<dt>Runtime:?</dt>\s*<dd>([^<]+)</dd>',
                webpage, 'duration', fatal=False))
        view_count = str_to_int(self._search_regex(
            (r'["\']viewsCount["\'][^>]*>(\d+)\s+views',
             r'<dt>Views:?</dt>\s*<dd>([\d,\.]+)</dd>'),
            webpage, 'view count', fatal=False))
        comment_count = str_to_int(self._html_search_regex(
            r'>Comments? \(([\d,\.]+)\)<',
            webpage, 'comment count', fatal=False))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'duration': duration,
            'view_count': view_count,
            'comment_count': comment_count,
            'age_limit': 18,
            'formats': formats,
        }