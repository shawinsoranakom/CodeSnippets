def _real_extract(self, url):
        video_id = self._match_id(url)
        video_id = video_id if video_id.isdigit() and len(video_id) > 6 else str(int(video_id, 36))

        # 'contentv4' is used in the website, but it also returns the related
        # videos, we don't need them
        # video_data = self._download_json(
        #     'http://www.wat.tv/interface/contentv4s/' + video_id, video_id)
        video_data = self._download_json(
            'https://mediainfo.tf1.fr/mediainfocombo/' + video_id,
            video_id, query={'pver': '5010000'})
        video_info = video_data['media']

        error_desc = video_info.get('error_desc')
        if error_desc:
            error_code = video_info.get('error_code')
            if error_code == 'GEOBLOCKED':
                self.raise_geo_restricted(error_desc, video_info.get('geoList'))
            elif error_code == 'DELIVERY_ERROR':
                if traverse_obj(video_data, ('delivery', 'code')) in (403, 500):
                    self.report_drm(video_id)
                error_desc = join_nonempty(
                    error_desc, traverse_obj(video_data, ('delivery', 'error', {str})), delim=': ')
            raise ExtractorError(error_desc, expected=True)

        title = video_info['title']

        formats = []
        subtitles = {}

        def extract_formats(manifest_urls):
            for f, f_url in manifest_urls.items():
                if not f_url:
                    continue
                if f in ('dash', 'mpd'):
                    fmts, subs = self._extract_mpd_formats_and_subtitles(
                        f_url.replace('://das-q1.tf1.fr/', '://das-q1-ssl.tf1.fr/'),
                        video_id, mpd_id='dash', fatal=False)
                elif f == 'hls':
                    fmts, subs = self._extract_m3u8_formats_and_subtitles(
                        f_url, video_id, 'mp4',
                        'm3u8_native', m3u8_id='hls', fatal=False)
                else:
                    continue
                formats.extend(fmts)
                self._merge_subtitles(subs, target=subtitles)

        delivery = video_data.get('delivery') or {}
        extract_formats({delivery.get('format'): delivery.get('url')})
        if not formats:
            if delivery.get('drm'):
                self.report_drm(video_id)
            manifest_urls = self._download_json(
                'http://www.wat.tv/get/webhtml/' + video_id, video_id, fatal=False)
            if manifest_urls:
                extract_formats(manifest_urls)

        return {
            'id': video_id,
            'title': title,
            'thumbnail': video_info.get('preview'),
            'upload_date': unified_strdate(try_get(
                video_data, lambda x: x['mediametrie']['chapters'][0]['estatS4'])),
            'duration': int_or_none(video_info.get('duration')),
            'formats': formats,
            'subtitles': subtitles,
        }