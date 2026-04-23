def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        server_id, camera_id = mobj.group('id'), mobj.group('camera_id')
        camera_name, description = None, None
        camera_url = compat_urlparse.urljoin(
            url, '/tv/camera/%s/%s/' % (server_id, camera_id))

        webpage = self._download_webpage(camera_url, server_id, fatal=False)
        if webpage:
            config_string = self._search_regex(
                r'var\s+config\s*=\s*({.+?});', webpage, 'config', default=None)
            if config_string:
                config = self._parse_json(config_string, server_id, fatal=False)
                camera_info = config.get('ivTvAppOptions', {}).get('currentCameraInfo')
                if camera_info:
                    camera_name = camera_info.get('camera_name')
                    description = camera_info.get('misc', {}).get('description')
            if not camera_name:
                camera_name = self._html_search_meta(
                    'name', webpage, 'camera name', default=None) or self._search_regex(
                    r'<h1[^>]+class="b-video-title"[^>]*>([^<]+)', webpage, 'camera name', default=None)

        quality = qualities(self._QUALITIES)

        formats = [{
            'url': 'https://streaming.ivideon.com/flv/live?%s' % compat_urllib_parse_urlencode({
                'server': server_id,
                'camera': camera_id,
                'sessionId': 'demo',
                'q': quality(format_id),
            }),
            'format_id': format_id,
            'ext': 'flv',
            'quality': quality(format_id),
        } for format_id in self._QUALITIES]
        self._sort_formats(formats)

        return {
            'id': server_id,
            'title': self._live_title(camera_name or server_id),
            'description': description,
            'is_live': True,
            'formats': formats,
        }