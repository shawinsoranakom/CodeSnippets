def _extract_aen_smil(self, smil_url, video_id, auth=None):
        query = {
            'mbr': 'true',
            'formats': 'M3U+none,MPEG-DASH+none,MPEG4,MP3',
        }
        if auth:
            query['auth'] = auth
        TP_SMIL_QUERY = [{
            'assetTypes': 'high_video_ak',
            'switch': 'hls_high_ak',
        }, {
            'assetTypes': 'high_video_s3',
        }, {
            'assetTypes': 'high_video_s3',
            'switch': 'hls_high_fastly',
        }]
        formats = []
        subtitles = {}
        last_e = None
        for q in TP_SMIL_QUERY:
            q.update(query)
            m_url = update_url_query(smil_url, q)
            m_url = self._sign_url(m_url, self._THEPLATFORM_KEY, self._THEPLATFORM_SECRET)
            try:
                tp_formats, tp_subtitles = self._extract_theplatform_smil(
                    m_url, video_id, 'Downloading %s SMIL data' % (q.get('switch') or q['assetTypes']))
            except ExtractorError as e:
                if isinstance(e, GeoRestrictedError):
                    raise
                last_e = e
                continue
            formats.extend(tp_formats)
            subtitles = self._merge_subtitles(subtitles, tp_subtitles)
        if last_e and not formats:
            raise last_e
        self._sort_formats(formats)
        return {
            'id': video_id,
            'formats': formats,
            'subtitles': subtitles,
        }