def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_extract_title(webpage) or self._html_search_meta(
            ['og:title', 'twitter:title'],
            webpage, 'title', default=None)

        video_id = self._search_regex((
            r'productId\s*=\s*([\'"])(?P<id>p\d+)\1',
            r'pproduct_id\s*=\s*([\'"])(?P<id>p\d+)\1',
            r'let\s+videos\s*=\s*([\'"])(?P<id>p\d+)\1',
        ), webpage, 'real id', group='id', default=None)

        if not video_id:
            nuxt_data = self._search_nuxt_data(webpage, video_id, traverse='data', fatal=False)
            video_id = traverse_obj(
                nuxt_data, (..., 'content', 'additionals', 'videoPlayId', {str}), get_all=False)

        if not video_id:
            nuxt_data = self._search_json(
                r'<script[^>]+\bid=["\']__NUXT_DATA__["\'][^>]*>',
                webpage, 'nuxt data', None, end_pattern=r'</script>', contains_pattern=r'\[(?s:.+)\]')

            video_id = traverse_obj(nuxt_data, lambda _, v: re.fullmatch(r'p\d+', v), get_all=False)

        if not video_id:
            self.raise_no_formats('Unable to extract video ID from webpage')

        metadata = self._download_json(
            f'https://api.play-backend.iprima.cz/api/v1//products/id-{video_id}/play',
            video_id, note='Getting manifest URLs', errnote='Failed to get manifest URLs',
            headers={'X-OTT-Access-Token': self.access_token},
            expected_status=403)

        self._raise_access_error(metadata.get('errorCode'))

        stream_infos = metadata.get('streamInfos')
        formats = []
        if stream_infos is None:
            self.raise_no_formats('Reading stream infos failed', expected=True)
        else:
            for manifest in stream_infos:
                manifest_type = manifest.get('type')
                manifest_url = manifest.get('url')
                ext = determine_ext(manifest_url)
                if manifest_type == 'HLS' or ext == 'm3u8':
                    formats += self._extract_m3u8_formats(
                        manifest_url, video_id, 'mp4', entry_protocol='m3u8_native',
                        m3u8_id='hls', fatal=False)
                elif manifest_type == 'DASH' or ext == 'mpd':
                    formats += self._extract_mpd_formats(
                        manifest_url, video_id, mpd_id='dash', fatal=False)

        final_result = self._search_json_ld(webpage, video_id, default={})
        final_result.update({
            'id': video_id,
            'title': final_result.get('title') or title,
            'thumbnail': self._html_search_meta(
                ['thumbnail', 'og:image', 'twitter:image'],
                webpage, 'thumbnail', default=None),
            'formats': formats,
            'description': self._html_search_meta(
                ['description', 'og:description', 'twitter:description'],
                webpage, 'description', default=None)})

        return final_result