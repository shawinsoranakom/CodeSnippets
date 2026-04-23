def _extract_formats(self, format_list, video_id):
        has_hls, has_dash = False, False

        for format_info in format_list or []:
            url = traverse_obj(format_info, ('tags', 'url'), 'url')
            if url is None:
                continue

            fmt_type = format_info.get('type') or 'unknown'
            transport = (format_info.get('transport') or 'https').lower()

            if transport == 'https':
                formats = [{
                    'url': url,
                    'abr': float_or_none(traverse_obj(format_info, ('audio', 'bitrate')), 1000),
                    'vbr': float_or_none(traverse_obj(format_info, ('video', 'bitrate')), 1000),
                    'fps': traverse_obj(format_info, ('video', 'framerate')),
                    **parse_resolution(traverse_obj(format_info, ('video', 'resolution'))),
                }]
            elif transport == 'hls':
                has_hls, formats = True, self._extract_m3u8_formats(
                    url, video_id, 'mp4', fatal=False, note=f'downloading {fmt_type} HLS manifest')
            elif transport == 'dash':
                has_dash, formats = True, self._extract_mpd_formats(
                    url, video_id, fatal=False, note=f'downloading {fmt_type} DASH manifest')
            else:
                # RTMP, HDS, SMOOTH, and unknown formats
                # - RTMP url fails on every tested entry until now
                # - HDS url 404's on every tested entry until now
                # - SMOOTH url 404's on every tested entry until now
                continue

            yield from self._set_format_type(formats, fmt_type)

        # TODO: Add test for these
        for fmt_type in self._FORMAT_TYPES:
            if not has_hls:
                hls_formats = self._extract_m3u8_formats(
                    f'https://wowza.tugraz.at/matterhorn_engage/smil:engage-player_{video_id}_{fmt_type}.smil/playlist.m3u8',
                    video_id, 'mp4', fatal=False, note=f'Downloading {fmt_type} HLS manifest', errnote=False) or []
                yield from self._set_format_type(hls_formats, fmt_type)

            if not has_dash:
                dash_formats = self._extract_mpd_formats(
                    f'https://wowza.tugraz.at/matterhorn_engage/smil:engage-player_{video_id}_{fmt_type}.smil/manifest_mpm4sav_mvlist.mpd',
                    video_id, fatal=False, note=f'Downloading {fmt_type} DASH manifest', errnote=False)
                yield from self._set_format_type(dash_formats, fmt_type)