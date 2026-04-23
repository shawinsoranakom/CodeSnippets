def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        kind, video_id, display_id = mobj.group('kind', 'id', 'display_id')

        if kind == 'm' or not display_id:
            url = self._URL_TEMPLATE % video_id

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_meta('name', webpage)
        timestamp = parse_iso8601(self._html_search_meta(
            'uploadDate', webpage))
        thumbnail = self._html_search_meta('thumbnailUrl', webpage)
        uploader_id = self._html_search_regex(
            r'<a class="item-to-subscribe" href="[^"]+/(?:channel|user)s?/([^/"]+)" title="Go to [^"]+ page">',
            webpage, 'uploader id', fatal=False)
        uploader = self._html_search_regex(
            r'<a class="item-to-subscribe" href="[^"]+/(?:channel|user)s?/[^/"]+" title="Go to ([^"]+) page">',
            webpage, 'uploader', fatal=False)

        categories_html = self._search_regex(
            r'(?s)><i class="icon icon-tag"></i>\s*Categories / Tags\s*.*?<ul class="[^"]*?list[^"]*?">(.*?)</ul>',
            webpage, 'categories', fatal=False)
        categories = None
        if categories_html:
            categories = [
                c.strip() for c in re.findall(
                    r'(?s)<li><a.*?>(.*?)</a>', categories_html)]

        view_count = str_to_int(self._search_regex(
            r'<meta[^>]+itemprop="interactionCount"[^>]+content="UserPlays:([0-9,]+)">',
            webpage, 'view count', default=None))
        like_count = str_to_int(self._search_regex(
            r'<meta[^>]+itemprop="interactionCount"[^>]+content="UserLikes:([0-9,]+)">',
            webpage, 'like count', default=None))
        duration = parse_duration(self._html_search_meta('duration', webpage))

        media_id = self._search_regex(
            r'<button[^>]+data-id=(["\'])(?P<id>\d+)\1[^>]+data-quality=', webpage,
            'media id', default=None, group='id')
        sources = [
            quality
            for _, quality in re.findall(r'<button[^>]+data-quality=(["\'])(.+?)\1', webpage)]
        if not (media_id and sources):
            player_js = self._download_webpage(
                self._search_regex(
                    r'<script[^>]id=(["\'])playerembed\1[^>]+src=(["\'])(?P<url>.+?)\2',
                    webpage, 'player JS', group='url'),
                video_id, 'Downloading player JS')
            params_js = self._search_regex(
                r'\$\.ajax\(url,\ opts\);\s*\}\s*\}\)\(([0-9,\[\] ]+)\)',
                player_js, 'initialization parameters')
            params = self._parse_json(f'[{params_js}]', video_id)
            media_id = params[0]
            sources = [f'{p}' for p in params[2]]

        formats = self._extract_formats(url, video_id, media_id, sources)

        return {
            'id': video_id,
            'title': title,
            'formats': formats,
            'categories': categories,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'timestamp': timestamp,
            'like_count': like_count,
            'view_count': view_count,
            'duration': duration,
            'age_limit': 18,
        }