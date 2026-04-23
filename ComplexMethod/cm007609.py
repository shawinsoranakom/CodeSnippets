def _extract_wowza_formats(self, url, video_id, m3u8_entry_protocol='m3u8_native', skip_protocols=[]):
        query = compat_urlparse.urlparse(url).query
        url = re.sub(r'/(?:manifest|playlist|jwplayer)\.(?:m3u8|f4m|mpd|smil)', '', url)
        mobj = re.search(
            r'(?:(?:http|rtmp|rtsp)(?P<s>s)?:)?(?P<url>//[^?]+)', url)
        url_base = mobj.group('url')
        http_base_url = '%s%s:%s' % ('http', mobj.group('s') or '', url_base)
        formats = []

        def manifest_url(manifest):
            m_url = '%s/%s' % (http_base_url, manifest)
            if query:
                m_url += '?%s' % query
            return m_url

        if 'm3u8' not in skip_protocols:
            formats.extend(self._extract_m3u8_formats(
                manifest_url('playlist.m3u8'), video_id, 'mp4',
                m3u8_entry_protocol, m3u8_id='hls', fatal=False))
        if 'f4m' not in skip_protocols:
            formats.extend(self._extract_f4m_formats(
                manifest_url('manifest.f4m'),
                video_id, f4m_id='hds', fatal=False))
        if 'dash' not in skip_protocols:
            formats.extend(self._extract_mpd_formats(
                manifest_url('manifest.mpd'),
                video_id, mpd_id='dash', fatal=False))
        if re.search(r'(?:/smil:|\.smil)', url_base):
            if 'smil' not in skip_protocols:
                rtmp_formats = self._extract_smil_formats(
                    manifest_url('jwplayer.smil'),
                    video_id, fatal=False)
                for rtmp_format in rtmp_formats:
                    rtsp_format = rtmp_format.copy()
                    rtsp_format['url'] = '%s/%s' % (rtmp_format['url'], rtmp_format['play_path'])
                    del rtsp_format['play_path']
                    del rtsp_format['ext']
                    rtsp_format.update({
                        'url': rtsp_format['url'].replace('rtmp://', 'rtsp://'),
                        'format_id': rtmp_format['format_id'].replace('rtmp', 'rtsp'),
                        'protocol': 'rtsp',
                    })
                    formats.extend([rtmp_format, rtsp_format])
        else:
            for protocol in ('rtmp', 'rtsp'):
                if protocol not in skip_protocols:
                    formats.append({
                        'url': '%s:%s' % (protocol, url_base),
                        'format_id': protocol,
                        'protocol': protocol,
                    })
        return formats