def _extract_formats(self, media_info, video_id):
        type_ = media_info.get('_type')
        media_array = media_info.get('_mediaArray', [])
        formats = []
        for num, media in enumerate(media_array):
            for stream in media.get('_mediaStreamArray', []):
                stream_urls = stream.get('_stream')
                if not stream_urls:
                    continue
                if not isinstance(stream_urls, list):
                    stream_urls = [stream_urls]
                quality = stream.get('_quality')
                server = stream.get('_server')
                for stream_url in stream_urls:
                    if not url_or_none(stream_url):
                        continue
                    ext = determine_ext(stream_url)
                    if quality != 'auto' and ext in ('f4m', 'm3u8'):
                        continue
                    if ext == 'f4m':
                        formats.extend(self._extract_f4m_formats(
                            update_url_query(stream_url, {
                                'hdcore': '3.1.1',
                                'plugin': 'aasp-3.1.1.69.124',
                            }), video_id, f4m_id='hds', fatal=False))
                    elif ext == 'm3u8':
                        formats.extend(self._extract_m3u8_formats(
                            stream_url, video_id, 'mp4', 'm3u8_native',
                            m3u8_id='hls', fatal=False))
                    else:
                        if server and server.startswith('rtmp'):
                            f = {
                                'url': server,
                                'play_path': stream_url,
                                'format_id': f'a{num}-rtmp-{quality}',
                            }
                        else:
                            f = {
                                'url': stream_url,
                                'format_id': f'a{num}-{ext}-{quality}',
                            }
                        m = re.search(
                            r'_(?P<width>\d+)x(?P<height>\d+)\.mp4$',
                            stream_url)
                        if m:
                            f.update({
                                'width': int(m.group('width')),
                                'height': int(m.group('height')),
                            })
                        if type_ == 'audio':
                            f['vcodec'] = 'none'
                        formats.append(f)
        return formats