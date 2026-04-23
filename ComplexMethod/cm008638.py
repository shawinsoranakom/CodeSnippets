def _extract_nbcu_formats_and_subtitles(self, tp_path, video_id, query):
        # formats='mpeg4' will return either a working m3u8 URL or an m3u8 template for non-DRM HLS
        # formats='m3u+none,mpeg4' may return DRM HLS but w/the "folders" needed for non-DRM template
        query['formats'] = 'm3u+none,mpeg4'
        orig_m3u8_url = m3u8_url = self._download_nbcu_smil_and_extract_m3u8_url(tp_path, video_id, query)

        if mobj := re.fullmatch(self._M3U8_RE, m3u8_url):
            query['formats'] = 'mpeg4'
            m3u8_tmpl = self._download_nbcu_smil_and_extract_m3u8_url(tp_path, video_id, query)
            # Example: https://vod-lf-oneapp-prd.akamaized.net/prod/video/{folders}master_hls.m3u8
            if '{folders}' in m3u8_tmpl:
                self.write_debug('Found m3u8 URL template, formatting URL path')
            m3u8_url = m3u8_tmpl.format(folders=mobj.group('folders'))

        if '/mpeg_cenc' in m3u8_url or '/mpeg_cbcs' in m3u8_url:
            self.report_drm(video_id)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False)

        if not formats and m3u8_url != orig_m3u8_url:
            orig_fmts, subtitles = self._extract_m3u8_formats_and_subtitles(
                orig_m3u8_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
            formats = [f for f in orig_fmts if not f.get('has_drm')]
            if orig_fmts and not formats:
                self.report_drm(video_id)

        return formats, subtitles