def _extract_info(self, pc, mobile, i, referer):
        get_item = lambda x, y: try_get(x, lambda x: x[y][i], dict) or {}
        pc_item = get_item(pc, 'playlistItems')
        mobile_item = get_item(mobile, 'mediaList')
        video_id = pc_item.get('mediaId') or mobile_item['mediaId']
        title = pc_item.get('title') or mobile_item['title']

        formats = []
        urls = []
        for stream in pc_item.get('streams', []):
            stream_url = stream.get('url')
            if not stream_url or stream.get('drmProtected') or stream_url in urls:
                continue
            urls.append(stream_url)
            ext = determine_ext(stream_url)
            if ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    stream_url, video_id, f4m_id='hds', fatal=False))
            else:
                fmt = {
                    'url': stream_url,
                    'abr': float_or_none(stream.get('audioBitRate')),
                    'fps': float_or_none(stream.get('videoFrameRate')),
                    'ext': ext,
                }
                width = int_or_none(stream.get('videoWidthInPixels'))
                height = int_or_none(stream.get('videoHeightInPixels'))
                vbr = float_or_none(stream.get('videoBitRate'))
                if width or height or vbr:
                    fmt.update({
                        'width': width,
                        'height': height,
                        'vbr': vbr,
                    })
                else:
                    fmt['vcodec'] = 'none'
                rtmp = re.search(r'^(?P<url>rtmpe?://(?P<host>[^/]+)/(?P<app>.+))/(?P<playpath>mp[34]:.+)$', stream_url)
                if rtmp:
                    format_id = 'rtmp'
                    if stream.get('videoBitRate'):
                        format_id += '-%d' % int_or_none(stream['videoBitRate'])
                    http_format_id = format_id.replace('rtmp', 'http')

                    CDN_HOSTS = (
                        ('delvenetworks.com', 'cpl.delvenetworks.com'),
                        ('video.llnw.net', 's2.content.video.llnw.net'),
                    )
                    for cdn_host, http_host in CDN_HOSTS:
                        if cdn_host not in rtmp.group('host').lower():
                            continue
                        http_url = 'http://%s/%s' % (http_host, rtmp.group('playpath')[4:])
                        urls.append(http_url)
                        if self._is_valid_url(http_url, video_id, http_format_id):
                            http_fmt = fmt.copy()
                            http_fmt.update({
                                'url': http_url,
                                'format_id': http_format_id,
                            })
                            formats.append(http_fmt)
                            break

                    fmt.update({
                        'url': rtmp.group('url'),
                        'play_path': rtmp.group('playpath'),
                        'app': rtmp.group('app'),
                        'ext': 'flv',
                        'format_id': format_id,
                    })
                formats.append(fmt)

        for mobile_url in mobile_item.get('mobileUrls', []):
            media_url = mobile_url.get('mobileUrl')
            format_id = mobile_url.get('targetMediaPlatform')
            if not media_url or format_id in ('Widevine', 'SmoothStreaming') or media_url in urls:
                continue
            urls.append(media_url)
            ext = determine_ext(media_url)
            if ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    media_url, video_id, 'mp4', 'm3u8_native',
                    m3u8_id=format_id, fatal=False))
            elif ext == 'f4m':
                formats.extend(self._extract_f4m_formats(
                    stream_url, video_id, f4m_id=format_id, fatal=False))
            else:
                formats.append({
                    'url': media_url,
                    'format_id': format_id,
                    'preference': -1,
                    'ext': ext,
                })

        self._sort_formats(formats)

        subtitles = {}
        for flag in mobile_item.get('flags'):
            if flag == 'ClosedCaptions':
                closed_captions = self._call_playlist_service(
                    video_id, 'getClosedCaptionsDetailsByMediaId',
                    False, referer) or []
                for cc in closed_captions:
                    cc_url = cc.get('webvttFileUrl')
                    if not cc_url:
                        continue
                    lang = cc.get('languageCode') or self._search_regex(r'/[a-z]{2}\.vtt', cc_url, 'lang', default='en')
                    subtitles.setdefault(lang, []).append({
                        'url': cc_url,
                    })
                break

        get_meta = lambda x: pc_item.get(x) or mobile_item.get(x)

        return {
            'id': video_id,
            'title': title,
            'description': get_meta('description'),
            'formats': formats,
            'duration': float_or_none(get_meta('durationInMilliseconds'), 1000),
            'thumbnail': get_meta('previewImageUrl') or get_meta('thumbnailImageUrl'),
            'subtitles': subtitles,
        }