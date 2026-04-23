def _extract_info(self, url, display_id):
        video_data = self._download_xml(url, display_id)
        video_id = xpath_text(video_data, 'id', fatal=True)
        episode_title = title = xpath_text(video_data, 'title', fatal=True)
        series = xpath_text(video_data, 'program')
        if series:
            title = f'{series} - {title}'

        formats = []
        for source in xpath_element(video_data, 'videos', 'sources', True):
            if source.tag == 'size':
                path = xpath_text(source, './/path')
                if not path:
                    continue
                width = source.attrib.get('width')
                format_info = self._FORMATS_INFO.get(width, {})
                height = format_info.get('height')
                fmt = {
                    'url': path,
                    'format_id': join_nonempty('http'. height and f'{height}p'),
                    'width': format_info.get('width'),
                    'height': height,
                }
                rtmp = re.search(r'^(?P<url>rtmpe?://[^/]+/(?P<app>.+))/(?P<playpath>mp4:.+)$', path)
                if rtmp:
                    fmt.update({
                        'url': rtmp.group('url'),
                        'play_path': rtmp.group('playpath'),
                        'app': rtmp.group('app'),
                        'ext': 'flv',
                        'format_id': fmt['format_id'].replace('http', 'rtmp'),
                    })
                formats.append(fmt)
            else:
                video_url = source.text
                if not video_url:
                    continue
                if source.tag == 'tarball':
                    formats.extend(self._extract_m3u8_formats(
                        video_url.replace('.tar', '/base_index_w8.m3u8'),
                        video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))
                elif source.tag == 'hls':
                    m3u8_formats = self._extract_m3u8_formats(
                        video_url.replace('.tar', '/base_index.m3u8'),
                        video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False)
                    for f in m3u8_formats:
                        if f.get('vcodec') == 'none' and not f.get('tbr'):
                            f['tbr'] = int_or_none(self._search_regex(
                                r'-(\d+)k/', f['url'], 'tbr', default=None))
                    formats.extend(m3u8_formats)
                elif source.tag == 'dash':
                    formats.extend(self._extract_mpd_formats(
                        video_url.replace('.tar', '/manifest.mpd'),
                        video_id, mpd_id='dash', fatal=False))
                else:
                    format_info = self._FORMATS_INFO.get(source.tag, {})
                    formats.append({
                        'format_id': f'http-{source.tag}',
                        'url': video_url,
                        'width': format_info.get('width'),
                        'height': format_info.get('height'),
                    })

        thumbnails = []
        card_sizes = xpath_element(video_data, 'titleCardSizes')
        if card_sizes is not None:
            for size in card_sizes:
                path = xpath_text(size, 'path')
                if not path:
                    continue
                width = int_or_none(size.get('width'))
                thumbnails.append({
                    'id': width,
                    'url': path,
                    'width': width,
                })

        subtitles = None
        caption_url = xpath_text(video_data, 'captionUrl')
        if caption_url:
            subtitles = {
                'en': [{
                    'url': caption_url,
                    'ext': 'ttml',
                }],
            }

        return {
            'id': video_id,
            'title': title,
            'duration': parse_duration(xpath_text(video_data, 'duration/tv14')),
            'series': series,
            'episode': episode_title,
            'formats': formats,
            'thumbnails': thumbnails,
            'subtitles': subtitles,
        }