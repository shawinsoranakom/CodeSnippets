def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        meta_id = mobj.group('metaid')

        video_id = None
        if meta_id:
            meta_url = f'https://my.mail.ru/+/video/meta/{meta_id}'
        else:
            video_id = mobj.group('idv1')
            if not video_id:
                video_id = mobj.group('idv2prefix') + mobj.group('idv2suffix')
            webpage = self._download_webpage(url, video_id)
            page_config = self._parse_json(self._search_regex([
                r'(?s)<script[^>]+class="sp-video__page-config"[^>]*>(.+?)</script>',
                r'(?s)"video":\s*({.+?}),'],
                webpage, 'page config', default='{}'), video_id, fatal=False)
            if page_config:
                meta_url = page_config.get('metaUrl') or page_config.get('video', {}).get('metaUrl') or page_config.get('metadataUrl')
            else:
                meta_url = None

        video_data = None

        # fix meta_url if missing the host address
        if re.match(r'\/\+\/', meta_url):
            meta_url = urljoin('https://my.mail.ru', meta_url)

        if meta_url:
            video_data = self._download_json(
                meta_url, video_id or meta_id, 'Downloading video meta JSON',
                fatal=not video_id)

        # Fallback old approach
        if not video_data:
            video_data = self._download_json(
                f'http://api.video.mail.ru/videos/{video_id}.json?new=1',
                video_id, 'Downloading video JSON')

        video_key = self._get_cookies('https://my.mail.ru').get('video_key')

        formats = []
        for f in video_data['videos']:
            video_url = f.get('url')
            if not video_url:
                continue
            if video_key:
                self._set_cookie(urllib.parse.urlparse(video_url).hostname, 'video_key', video_key.value)
            format_id = f.get('key')
            height = int_or_none(self._search_regex(
                r'^(\d+)[pP]$', format_id, 'height', default=None)) if format_id else None
            formats.append({
                'url': video_url,
                'format_id': format_id,
                'height': height,
            })

        meta_data = video_data['meta']
        title = remove_end(meta_data['title'], '.mp4')

        author = video_data.get('author')
        uploader = author.get('name')
        uploader_id = author.get('id') or author.get('email')
        view_count = int_or_none(video_data.get('viewsCount') or video_data.get('views_count'))

        acc_id = meta_data.get('accId')
        item_id = meta_data.get('itemId')
        content_id = f'{acc_id}_{item_id}' if acc_id and item_id else video_id

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