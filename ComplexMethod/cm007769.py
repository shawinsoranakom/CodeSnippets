def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        meta_id = mobj.group('metaid')

        video_id = None
        if meta_id:
            meta_url = 'https://my.mail.ru/+/video/meta/%s' % meta_id
        else:
            video_id = mobj.group('idv1')
            if not video_id:
                video_id = mobj.group('idv2prefix') + mobj.group('idv2suffix')
            webpage = self._download_webpage(url, video_id)
            page_config = self._parse_json(self._search_regex(
                r'(?s)<script[^>]+class="sp-video__page-config"[^>]*>(.+?)</script>',
                webpage, 'page config', default='{}'), video_id, fatal=False)
            if page_config:
                meta_url = page_config.get('metaUrl') or page_config.get('video', {}).get('metaUrl')
            else:
                meta_url = None

        video_data = None
        if meta_url:
            video_data = self._download_json(
                meta_url, video_id or meta_id, 'Downloading video meta JSON',
                fatal=not video_id)

        # Fallback old approach
        if not video_data:
            video_data = self._download_json(
                'http://api.video.mail.ru/videos/%s.json?new=1' % video_id,
                video_id, 'Downloading video JSON')

        headers = {}

        video_key = self._get_cookies('https://my.mail.ru').get('video_key')
        if video_key:
            headers['Cookie'] = 'video_key=%s' % video_key.value

        formats = []
        for f in video_data['videos']:
            video_url = f.get('url')
            if not video_url:
                continue
            format_id = f.get('key')
            height = int_or_none(self._search_regex(
                r'^(\d+)[pP]$', format_id, 'height', default=None)) if format_id else None
            formats.append({
                'url': video_url,
                'format_id': format_id,
                'height': height,
                'http_headers': headers,
            })
        self._sort_formats(formats)

        meta_data = video_data['meta']
        title = remove_end(meta_data['title'], '.mp4')

        author = video_data.get('author')
        uploader = author.get('name')
        uploader_id = author.get('id') or author.get('email')
        view_count = int_or_none(video_data.get('viewsCount') or video_data.get('views_count'))

        acc_id = meta_data.get('accId')
        item_id = meta_data.get('itemId')
        content_id = '%s_%s' % (acc_id, item_id) if acc_id and item_id else video_id

        thumbnail = meta_data.get('poster')
        duration = int_or_none(meta_data.get('duration'))
        timestamp = int_or_none(meta_data.get('timestamp'))

        return {
            'id': content_id,
            'title': title,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'duration': duration,
            'view_count': view_count,
            'formats': formats,
        }