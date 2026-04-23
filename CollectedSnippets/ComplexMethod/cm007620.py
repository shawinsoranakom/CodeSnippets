def _real_extract(self, url):
        video_id = self._match_id(url)

        formats = []
        for encoding_format in ('m3u8', 'mpd'):
            media = self._call_api('media/' + video_id, video_id, query={
                'encodingsNew': 'true',
                'encodingsFormat': encoding_format,
            })
            for encoding in media.get('encodings', []):
                playlist_url = encoding.get('master_playlist_url')
                if encoding_format == 'm3u8':
                    # use `m3u8` entry_protocol until EXT-X-MAP is properly supported by `m3u8_native` entry_protocol
                    formats.extend(self._extract_m3u8_formats(
                        playlist_url, video_id, 'mp4',
                        m3u8_id='hls', fatal=False))
                elif encoding_format == 'mpd':
                    formats.extend(self._extract_mpd_formats(
                        playlist_url, video_id, mpd_id='dash', fatal=False))
                encoding_url = encoding.get('url')
                file_url = encoding.get('file_url')
                if not encoding_url and not file_url:
                    continue
                f = {
                    'width': int_or_none(encoding.get('width')),
                    'height': int_or_none(encoding.get('height')),
                    'vbr': int_or_none(encoding.get('video_bitrate')),
                    'abr': int_or_none(encoding.get('audio_bitrate')),
                    'filesize': int_or_none(encoding.get('size_in_bytes')),
                    'vcodec': encoding.get('video_codec'),
                    'acodec': encoding.get('audio_codec'),
                    'container': encoding.get('container_type'),
                }
                for f_url in (encoding_url, file_url):
                    if not f_url:
                        continue
                    fmt = f.copy()
                    rtmp = re.search(r'^(?P<url>rtmpe?://(?P<host>[^/]+)/(?P<app>.+))/(?P<playpath>mp[34]:.+)$', f_url)
                    if rtmp:
                        fmt.update({
                            'url': rtmp.group('url'),
                            'play_path': rtmp.group('playpath'),
                            'app': rtmp.group('app'),
                            'ext': 'flv',
                            'format_id': 'rtmp',
                        })
                    else:
                        fmt.update({
                            'url': f_url,
                            'format_id': 'http',
                        })
                    formats.append(fmt)
        self._sort_formats(formats)

        title = media['title']

        subtitles = {}
        for closed_caption in media.get('closed_captions', []):
            sub_url = closed_caption.get('file')
            if not sub_url:
                continue
            lang = closed_caption.get('code') or closed_caption.get('language') or 'en'
            subtitles.setdefault(lang, []).append({
                'url': sub_url,
            })

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': media.get('description'),
            'thumbnail': media.get('image_large') or media.get('image_medium') or media.get('image_small'),
            'duration': int_or_none(media.get('duration')),
            'tags': media.get('tags'),
            'subtitles': subtitles,
        }