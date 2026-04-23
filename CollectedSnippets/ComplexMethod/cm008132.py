def _extract_thumbnails(self, video_id):
        try_all = 'thumbnails' in self._configuration_arg('check_all')
        thumbnail_base_urls = ['http://{server}/vi{webp}/{video_id}'.format(
            webp='_webp' if ext == 'webp' else '', video_id=video_id, server=server)
            for server in (self._YT_ALL_THUMB_SERVERS if try_all else self._YT_DEFAULT_THUMB_SERVERS) for ext in (('jpg', 'webp') if try_all else ('jpg',))]

        thumbnails = []
        for url in thumbnail_base_urls:
            response = self._call_cdx_api(
                video_id, url, filters=['mimetype:image/(?:webp|jpeg)'],
                collapse=['urlkey'], query={'matchType': 'prefix'})
            if not response:
                continue
            thumbnails.extend(
                {
                    'url': (self._WAYBACK_BASE_URL % (int_or_none(thumbnail_dict.get('timestamp')) or self._OLDEST_CAPTURE_DATE)) + thumbnail_dict.get('original'),
                    'filesize': int_or_none(thumbnail_dict.get('length')),
                    'preference': int_or_none(thumbnail_dict.get('length')),
                } for thumbnail_dict in response)
            if not try_all:
                break

        self._remove_duplicate_formats(thumbnails)
        return thumbnails