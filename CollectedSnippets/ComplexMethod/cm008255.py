def _parse_mediapackage(self, video):
        video_id = video.get('id')
        if video_id is None:
            raise ExtractorError('Video id was not found')

        formats = []
        for track in variadic(traverse_obj(video, ('media', 'track')) or []):
            href = track.get('url')
            if href is None:
                continue
            ext = determine_ext(href, None)

            transport = track.get('transport')

            if transport == 'DASH' or ext == 'mpd':
                formats.extend(self._extract_mpd_formats(href, video_id, mpd_id='dash', fatal=False))
            elif transport == 'HLS' or ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    href, video_id, m3u8_id='hls', entry_protocol='m3u8_native', fatal=False))
            elif transport == 'HDS' or ext == 'f4m':
                formats.extend(self._extract_f4m_formats(href, video_id, f4m_id='hds', fatal=False))
            elif transport == 'SMOOTH':
                formats.extend(self._extract_ism_formats(href, video_id, ism_id='smooth', fatal=False))
            elif ext == 'smil':
                formats.extend(self._extract_smil_formats(href, video_id, fatal=False))
            else:
                track_obj = {
                    'url': href,
                    'ext': ext,
                    'format_note': track.get('transport'),
                    'resolution': traverse_obj(track, ('video', 'resolution')),
                    'fps': int_or_none(traverse_obj(track, ('video', 'framerate'))),
                    'vbr': int_or_none(traverse_obj(track, ('video', 'bitrate')), scale=1000),
                    'vcodec': traverse_obj(track, ('video', 'encoder', 'type')) if track.get('video') else 'none',
                    'abr': int_or_none(traverse_obj(track, ('audio', 'bitrate')), scale=1000),
                    'asr': int_or_none(traverse_obj(track, ('audio', 'samplingrate'))),
                    'acodec': traverse_obj(track, ('audio', 'encoder', 'type')) if track.get('audio') else 'none',
                }

                if transport == 'RTMP':
                    m_obj = re.search(r'(?:rtmp://[^/]+/(?P<app>[^/]+))/(?P<ext>.+):(?P<playpath>.+)', href)
                    if not m_obj:
                        continue
                    track_obj.update({
                        'app': m_obj.group('app'),
                        'ext': m_obj.group('ext'),
                        'play_path': m_obj.group('ext') + ':' + m_obj.group('playpath'),
                        'rtmp_live': True,
                        'preference': -2,
                    })
                formats.append(track_obj)

        return {
            'id': video_id,
            'formats': formats,
            'title': video.get('title'),
            'series': video.get('seriestitle'),
            'season_id': video.get('series'),
            'creator': traverse_obj(video, ('creators', 'creator')),
            'timestamp': parse_iso8601(video.get('start')),
            'thumbnail': traverse_obj(video, ('attachments', 'attachment', ..., 'url'), get_all=False),
        }