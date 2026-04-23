def _real_extract(self, url):
        video_id = self._match_id(url)

        video = self._download_json(
            f'http://mam.eitb.eus/mam/REST/ServiceMultiweb/Video/MULTIWEBTV/{video_id}/',
            video_id, 'Downloading video JSON')

        media = video['web_media'][0]

        formats = []
        for rendition in media['RENDITIONS']:
            video_url = rendition.get('PMD_URL')
            if not video_url:
                continue
            tbr = float_or_none(rendition.get('ENCODING_RATE'), 1000)
            formats.append({
                'url': rendition['PMD_URL'],
                'format_id': join_nonempty('http', int_or_none(tbr)),
                'width': int_or_none(rendition.get('FRAME_WIDTH')),
                'height': int_or_none(rendition.get('FRAME_HEIGHT')),
                'tbr': tbr,
            })

        hls_url = media.get('HLS_SURL')
        if hls_url:
            request = Request(
                'http://mam.eitb.eus/mam/REST/ServiceMultiweb/DomainRestrictedSecurity/TokenAuth/',
                headers={'Referer': url})
            token_data = self._download_json(
                request, video_id, 'Downloading auth token', fatal=False)
            if token_data:
                token = token_data.get('token')
                if token:
                    formats.extend(self._extract_m3u8_formats(
                        f'{hls_url}?hdnts={token}', video_id, m3u8_id='hls', fatal=False))

        hds_url = media.get('HDS_SURL')
        if hds_url:
            formats.extend(self._extract_f4m_formats(
                '{}?hdcore=3.7.0'.format(hds_url.replace('euskalsvod', 'euskalvod')),
                video_id, f4m_id='hds', fatal=False))

        return {
            'id': video_id,
            'title': media.get('NAME_ES') or media.get('name') or media['NAME_EU'],
            'description': media.get('SHORT_DESC_ES') or video.get('desc_group') or media.get('SHORT_DESC_EU'),
            'thumbnail': media.get('STILL_URL') or media.get('THUMBNAIL_URL'),
            'duration': float_or_none(media.get('LENGTH'), 1000),
            'timestamp': parse_iso8601(media.get('BROADCST_DATE'), ' '),
            'tags': media.get('TAGS'),
            'formats': formats,
        }