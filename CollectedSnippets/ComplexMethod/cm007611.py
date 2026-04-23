def _parse_jwplayer_formats(self, jwplayer_sources_data, video_id=None,
                                m3u8_id=None, mpd_id=None, rtmp_params=None, base_url=None):
        urls = set()
        formats = []
        for source in jwplayer_sources_data:
            if not isinstance(source, dict):
                continue
            source_url = urljoin(
                base_url, self._proto_relative_url(source.get('file')))
            if not source_url or source_url in urls:
                continue
            urls.add(source_url)
            source_type = source.get('type') or ''
            ext = mimetype2ext(source_type) or determine_ext(source_url)
            if source_type == 'hls' or ext == 'm3u8' or 'format=m3u8-aapl' in source_url:
                formats.extend(self._extract_m3u8_formats(
                    source_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id=m3u8_id, fatal=False))
            elif source_type == 'dash' or ext == 'mpd' or 'format=mpd-time-csf' in source_url:
                formats.extend(self._extract_mpd_formats(
                    source_url, video_id, mpd_id=mpd_id, fatal=False))
            elif ext == 'smil':
                formats.extend(self._extract_smil_formats(
                    source_url, video_id, fatal=False))
            # https://github.com/jwplayer/jwplayer/blob/master/src/js/providers/default.js#L67
            elif source_type.startswith('audio') or ext in (
                    'oga', 'aac', 'mp3', 'mpeg', 'vorbis'):
                formats.append({
                    'url': source_url,
                    'vcodec': 'none',
                    'ext': ext,
                })
            else:
                format_id = str_or_none(source.get('label'))
                height = int_or_none(source.get('height'))
                if height is None and format_id:
                    # Often no height is provided but there is a label in
                    # format like "1080p", "720p SD", or 1080.
                    height = parse_resolution(format_id).get('height')
                a_format = {
                    'url': source_url,
                    'width': int_or_none(source.get('width')),
                    'height': height,
                    'tbr': int_or_none(source.get('bitrate'), scale=1000),
                    'filesize': int_or_none(source.get('filesize')),
                    'ext': ext,
                }
                if format_id:
                    a_format['format_id'] = format_id

                if source_url.startswith('rtmp'):
                    a_format['ext'] = 'flv'
                    # See com/longtailvideo/jwplayer/media/RTMPMediaProvider.as
                    # of jwplayer.flash.swf
                    rtmp_url_parts = re.split(
                        r'((?:mp4|mp3|flv):)', source_url, maxsplit=1)
                    if len(rtmp_url_parts) == 3:
                        rtmp_url, prefix, play_path = rtmp_url_parts
                        a_format.update({
                            'url': rtmp_url,
                            'play_path': prefix + play_path,
                        })
                    if rtmp_params:
                        a_format.update(rtmp_params)
                formats.append(a_format)
        return formats