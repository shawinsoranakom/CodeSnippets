def _parse_smil_formats(self, smil, smil_url, video_id, namespace=None, f4m_params=None, transform_rtmp_url=None):
        base = smil_url
        for meta in smil.findall(self._xpath_ns('./head/meta', namespace)):
            b = meta.get('base') or meta.get('httpBase')
            if b:
                base = b
                break

        formats = []
        rtmp_count = 0
        http_count = 0
        m3u8_count = 0

        srcs = []
        media = smil.findall(self._xpath_ns('.//video', namespace)) + smil.findall(self._xpath_ns('.//audio', namespace))
        for medium in media:
            src = medium.get('src')
            if not src or src in srcs:
                continue
            srcs.append(src)

            bitrate = float_or_none(medium.get('system-bitrate') or medium.get('systemBitrate'), 1000)
            filesize = int_or_none(medium.get('size') or medium.get('fileSize'))
            width = int_or_none(medium.get('width'))
            height = int_or_none(medium.get('height'))
            proto = medium.get('proto')
            ext = medium.get('ext')
            src_ext = determine_ext(src)
            streamer = medium.get('streamer') or base

            if proto == 'rtmp' or streamer.startswith('rtmp'):
                rtmp_count += 1
                formats.append({
                    'url': streamer,
                    'play_path': src,
                    'ext': 'flv',
                    'format_id': 'rtmp-%d' % (rtmp_count if bitrate is None else bitrate),
                    'tbr': bitrate,
                    'filesize': filesize,
                    'width': width,
                    'height': height,
                })
                if transform_rtmp_url:
                    streamer, src = transform_rtmp_url(streamer, src)
                    formats[-1].update({
                        'url': streamer,
                        'play_path': src,
                    })
                continue

            src_url = src if src.startswith('http') else compat_urlparse.urljoin(base, src)
            src_url = src_url.strip()

            if proto == 'm3u8' or src_ext == 'm3u8':
                m3u8_formats = self._extract_m3u8_formats(
                    src_url, video_id, ext or 'mp4', m3u8_id='hls', fatal=False)
                if len(m3u8_formats) == 1:
                    m3u8_count += 1
                    m3u8_formats[0].update({
                        'format_id': 'hls-%d' % (m3u8_count if bitrate is None else bitrate),
                        'tbr': bitrate,
                        'width': width,
                        'height': height,
                    })
                formats.extend(m3u8_formats)
            elif src_ext == 'f4m':
                f4m_url = src_url
                if not f4m_params:
                    f4m_params = {
                        'hdcore': '3.2.0',
                        'plugin': 'flowplayer-3.2.0.1',
                    }
                f4m_url += '&' if '?' in f4m_url else '?'
                f4m_url += compat_urllib_parse_urlencode(f4m_params)
                formats.extend(self._extract_f4m_formats(f4m_url, video_id, f4m_id='hds', fatal=False))
            elif src_ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    src_url, video_id, mpd_id='dash', fatal=False))
            elif re.search(r'\.ism/[Mm]anifest', src_url):
                formats.extend(self._extract_ism_formats(
                    src_url, video_id, ism_id='mss', fatal=False))
            elif src_url.startswith('http') and self._is_valid_url(src, video_id):
                http_count += 1
                formats.append({
                    'url': src_url,
                    'ext': ext or src_ext or 'flv',
                    'format_id': 'http-%d' % (bitrate or http_count),
                    'tbr': bitrate,
                    'filesize': filesize,
                    'width': width,
                    'height': height,
                })

        return formats