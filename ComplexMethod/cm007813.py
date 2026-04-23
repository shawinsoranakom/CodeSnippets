def _real_extract(self, url):
        video_id = self._match_id(url)
        video_id = video_id if video_id.isdigit() and len(video_id) > 6 else compat_str(int(video_id, 36))

        # 'contentv4' is used in the website, but it also returns the related
        # videos, we don't need them
        # video_data = self._download_json(
        #     'http://www.wat.tv/interface/contentv4s/' + video_id, video_id)
        video_data = self._download_json(
            'https://mediainfo.tf1.fr/mediainfocombo/' + video_id,
            video_id, query={'context': 'MYTF1', 'pver': '4001000'})
        video_info = video_data['media']

        error_desc = video_info.get('error_desc')
        if error_desc:
            if video_info.get('error_code') == 'GEOBLOCKED':
                self.raise_geo_restricted(error_desc, video_info.get('geoList'))
            raise ExtractorError(error_desc, expected=True)

        title = video_info['title']

        formats = []

        def extract_formats(manifest_urls):
            for f, f_url in manifest_urls.items():
                if not f_url:
                    continue
                if f in ('dash', 'mpd'):
                    formats.extend(self._extract_mpd_formats(
                        f_url.replace('://das-q1.tf1.fr/', '://das-q1-ssl.tf1.fr/'),
                        video_id, mpd_id='dash', fatal=False))
                elif f == 'hls':
                    formats.extend(self._extract_m3u8_formats(
                        f_url, video_id, 'mp4',
                        'm3u8_native', m3u8_id='hls', fatal=False))

        delivery = video_data.get('delivery') or {}
        extract_formats({delivery.get('format'): delivery.get('url')})
        if not formats:
            if delivery.get('drm'):
                raise ExtractorError('This video is DRM protected.', expected=True)
            manifest_urls = self._download_json(
                'http://www.wat.tv/get/webhtml/' + video_id, video_id, fatal=False)
            if manifest_urls:
                extract_formats(manifest_urls)

        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': video_info.get('preview'),
            'upload_date': unified_strdate(try_get(
                video_data, lambda x: x['mediametrie']['chapters'][0]['estatS4'])),
            'duration': int_or_none(video_info.get('duration')),
            'formats': formats,
        }