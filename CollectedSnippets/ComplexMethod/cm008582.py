def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        def get(meta, default=NO_DEFAULT, fatal=True):
            return self._search_regex(
                rf'set{meta}\s*\(\s*(["\'])(?P<value>(?:(?!\1).)+)\1',
                webpage, meta, default=default, fatal=fatal, group='value')

        title = self._og_search_title(
            webpage, default=None) or get('VideoTitle')

        formats = []
        for mobj in re.finditer(
                r'setVideo(?:Url(?P<id>Low|High)|HLS)\s*\(\s*(?P<q>["\'])(?P<url>(?:https?:)?//.+?)(?P=q)', webpage):
            format_url = mobj.group('url')
            if determine_ext(format_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    quality=1, m3u8_id='hls', fatal=False))
            else:
                format_id = mobj.group('id')
                if format_id:
                    format_id = format_id.lower()
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                    'quality': -1 if format_id == 'low' else 0,
                })

        thumbnail = self._og_search_thumbnail(webpage, default=None) or get(
            'ThumbUrl', fatal=False) or get('ThumbUrl169', fatal=False)
        duration = int_or_none(self._og_search_property('duration', webpage))
        view_count = str_to_int(self._search_regex(
            r'id=["\']nb-views-number[^>]+>([\d,.]+)', webpage, 'view count',
            default=None))

        return {
            'id': video_id,
            'title': title,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'age_limit': 18,
            'formats': formats,
        }