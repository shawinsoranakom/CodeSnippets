def _extract_akamai_formats(self, manifest_url, video_id, hosts={}):
        signed = 'hdnea=' in manifest_url
        if not signed:
            # https://learn.akamai.com/en-us/webhelp/media-services-on-demand/stream-packaging-user-guide/GUID-BE6C0F73-1E06-483B-B0EA-57984B91B7F9.html
            manifest_url = re.sub(
                r'(?:b=[\d,-]+|(?:__a__|attributes)=off|__b__=\d+)&?',
                '', manifest_url).strip('?')

        formats = []

        hdcore_sign = 'hdcore=3.7.0'
        f4m_url = re.sub(r'(https?://[^/]+)/i/', r'\1/z/', manifest_url).replace('/master.m3u8', '/manifest.f4m')
        hds_host = hosts.get('hds')
        if hds_host:
            f4m_url = re.sub(r'(https?://)[^/]+', r'\1' + hds_host, f4m_url)
        if 'hdcore=' not in f4m_url:
            f4m_url += ('&' if '?' in f4m_url else '?') + hdcore_sign
        f4m_formats = self._extract_f4m_formats(
            f4m_url, video_id, f4m_id='hds', fatal=False)
        for entry in f4m_formats:
            entry.update({'extra_param_to_segment_url': hdcore_sign})
        formats.extend(f4m_formats)

        m3u8_url = re.sub(r'(https?://[^/]+)/z/', r'\1/i/', manifest_url).replace('/manifest.f4m', '/master.m3u8')
        hls_host = hosts.get('hls')
        if hls_host:
            m3u8_url = re.sub(r'(https?://)[^/]+', r'\1' + hls_host, m3u8_url)
        m3u8_formats = self._extract_m3u8_formats(
            m3u8_url, video_id, 'mp4', 'm3u8_native',
            m3u8_id='hls', fatal=False)
        formats.extend(m3u8_formats)

        http_host = hosts.get('http')
        if http_host and m3u8_formats and not signed:
            REPL_REGEX = r'https?://[^/]+/i/([^,]+),([^/]+),([^/]+)\.csmil/.+'
            qualities = re.match(REPL_REGEX, m3u8_url).group(2).split(',')
            qualities_length = len(qualities)
            if len(m3u8_formats) in (qualities_length, qualities_length + 1):
                i = 0
                for f in m3u8_formats:
                    if f['vcodec'] != 'none':
                        for protocol in ('http', 'https'):
                            http_f = f.copy()
                            del http_f['manifest_url']
                            http_url = re.sub(
                                REPL_REGEX, protocol + r'://%s/\g<1>%s\3' % (http_host, qualities[i]), f['url'])
                            http_f.update({
                                'format_id': http_f['format_id'].replace('hls-', protocol + '-'),
                                'url': http_url,
                                'protocol': protocol,
                            })
                            formats.append(http_f)
                        i += 1

        return formats