def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        mobj = re.search(r'<a\s+href="(?P<url>[^"]+)"\s+data-duration="\d+"\s+title="Download audio directly">', webpage)
        if mobj:
            urls_info = mobj.groupdict()
            youtube = False
            video = False
        else:
            mobj = re.search(r'<a href="(?P<url>http://www\.youtube\.com/watch\?v=[^"]+)"><span><strong>External Link:</strong>',
                             webpage)
            if mobj is None:
                mobj = re.search(r'<iframe width="100%" src="(?P<url>//www\.youtube-nocookie\.com/embed/[^?"]+)', webpage)
            if mobj:
                urls_info = mobj.groupdict()
                youtube = True
                video = True

        if mobj is None:
            mobj = re.search(r'(?P<type>)"(?:sources|files|renditions)":\s*(?P<json_data>\[[^\]]+\])', webpage)
            if mobj is None:
                mobj = re.search(
                    r'inline(?P<type>Video|Audio|YouTube)Data\.push\((?P<json_data>[^)]+)\);',
                    webpage)
                if mobj is None:
                    expired = self._html_search_regex(r'(?s)class="expired-(?:video|audio)".+?<span>(.+?)</span>', webpage, 'expired', None)
                    if expired:
                        raise ExtractorError(f'{self.IE_NAME} said: {expired}', expected=True)
                    raise ExtractorError('Unable to extract video urls')

            urls_info = self._parse_json(
                mobj.group('json_data'), video_id, transform_source=js_to_json)
            youtube = mobj.group('type') == 'YouTube'
            video = mobj.group('type') == 'Video' or traverse_obj(
                urls_info, (0, ('contentType', 'MIMEType')), get_all=False) == 'video/mp4'

        if not isinstance(urls_info, list):
            urls_info = [urls_info]

        if youtube:
            return self.playlist_result([
                self.url_result(url_info['url']) for url_info in urls_info])

        formats = []
        for url_info in urls_info:
            height = int_or_none(url_info.get('height'))
            bitrate = int_or_none(url_info.get('bitrate'))
            width = int_or_none(url_info.get('width'))
            format_id = None
            mobj = re.search(r'_(?:(?P<height>\d+)|(?P<bitrate>\d+)k)\.mp4$', url_info['url'])
            if mobj:
                height_from_url = mobj.group('height')
                if height_from_url:
                    height = height or int_or_none(height_from_url)
                    width = width or int_or_none(url_info.get('label'))
                else:
                    bitrate = bitrate or int_or_none(mobj.group('bitrate'))
                    format_id = str_or_none(url_info.get('label'))
            formats.append({
                'url': url_info['url'],
                'vcodec': url_info.get('codec') if video else 'none',
                'width': width,
                'height': height,
                'tbr': bitrate,
                'filesize': int_or_none(url_info.get('filesize')),
                'format_id': format_id,
            })

        return {
            'id': video_id,
            'title': self._og_search_title(webpage),
            'formats': formats,
            'description': self._og_search_description(webpage),
            'thumbnail': self._og_search_thumbnail(webpage),
        }