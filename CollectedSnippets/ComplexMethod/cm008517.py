def get_formats(format_url, format_id, quality):
            if not format_url:
                return
            ext = determine_ext(format_url)
            query = urllib.parse.urlparse(format_url).query

            if ext == 'm3u8':
                # Extract pre-merged HLS formats to avoid buggy parsing of metadata in split playlists
                format_url = format_url.replace('-split.m3u8', '.m3u8')
                m3u8_formats = self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', m3u8_id=f'hls-{format_id}', fatal=False, quality=quality)
                # Sometimes only split video/audio formats are available, need to fixup video-only formats
                is_not_premerged = 'none' in traverse_obj(m3u8_formats, (..., 'vcodec'))
                for fmt in m3u8_formats:
                    if is_not_premerged and fmt.get('vcodec') != 'none':
                        fmt['acodec'] = 'none'
                    yield {
                        **fmt,
                        'url': update_url(fmt['url'], query=query),
                        'extra_param_to_segment_url': query,
                    }

            elif ext == 'mpd':
                dash_formats = self._extract_mpd_formats(
                    format_url, video_id, mpd_id=f'dash-{format_id}', fatal=False)
                for fmt in dash_formats:
                    yield {
                        **fmt,
                        'extra_param_to_segment_url': query,
                        'quality': quality,
                    }

            else:
                yield {
                    'url': format_url,
                    'ext': ext,
                    'format_id': f'http-{format_id}',
                    'quality': quality,
                    **video_properties,
                }