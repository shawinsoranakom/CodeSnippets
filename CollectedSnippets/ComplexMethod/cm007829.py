def _parse_brightcove_metadata(self, json_data, video_id, headers={}):
        title = json_data['name'].strip()

        num_drm_sources = 0
        formats = []
        sources = json_data.get('sources') or []
        for source in sources:
            container = source.get('container')
            ext = mimetype2ext(source.get('type'))
            src = source.get('src')
            # https://support.brightcove.com/playback-api-video-fields-reference#key_systems_object
            if container == 'WVM' or source.get('key_systems'):
                num_drm_sources += 1
                continue
            elif ext == 'ism':
                continue
            elif ext == 'm3u8' or container == 'M2TS':
                if not src:
                    continue
                formats.extend(self._extract_m3u8_formats(
                    src, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False))
            elif ext == 'mpd':
                if not src:
                    continue
                formats.extend(self._extract_mpd_formats(src, video_id, 'dash', fatal=False))
            else:
                streaming_src = source.get('streaming_src')
                stream_name, app_name = source.get('stream_name'), source.get('app_name')
                if not src and not streaming_src and (not stream_name or not app_name):
                    continue
                tbr = float_or_none(source.get('avg_bitrate'), 1000)
                height = int_or_none(source.get('height'))
                width = int_or_none(source.get('width'))
                f = {
                    'tbr': tbr,
                    'filesize': int_or_none(source.get('size')),
                    'container': container,
                    'ext': ext or container.lower(),
                }
                if width == 0 and height == 0:
                    f.update({
                        'vcodec': 'none',
                    })
                else:
                    f.update({
                        'width': width,
                        'height': height,
                        'vcodec': source.get('codec'),
                    })

                def build_format_id(kind):
                    format_id = kind
                    if tbr:
                        format_id += '-%dk' % int(tbr)
                    if height:
                        format_id += '-%dp' % height
                    return format_id

                if src or streaming_src:
                    f.update({
                        'url': src or streaming_src,
                        'format_id': build_format_id('http' if src else 'http-streaming'),
                        'source_preference': 0 if src else -1,
                    })
                else:
                    f.update({
                        'url': app_name,
                        'play_path': stream_name,
                        'format_id': build_format_id('rtmp'),
                    })
                formats.append(f)

        if not formats:
            errors = json_data.get('errors')
            if errors:
                error = errors[0]
                raise ExtractorError(
                    error.get('message') or error.get('error_subcode') or error['error_code'], expected=True)
            if sources and num_drm_sources == len(sources):
                raise ExtractorError('This video is DRM protected.', expected=True)

        self._sort_formats(formats)

        for f in formats:
            f.setdefault('http_headers', {}).update(headers)

        subtitles = {}
        for text_track in json_data.get('text_tracks', []):
            if text_track.get('kind') != 'captions':
                continue
            text_track_url = url_or_none(text_track.get('src'))
            if not text_track_url:
                continue
            lang = (str_or_none(text_track.get('srclang'))
                    or str_or_none(text_track.get('label')) or 'en').lower()
            subtitles.setdefault(lang, []).append({
                'url': text_track_url,
            })

        is_live = False
        duration = float_or_none(json_data.get('duration'), 1000)
        if duration is not None and duration <= 0:
            is_live = True

        return {
            'id': video_id,
            'title': self._live_title(title) if is_live else title,
            'description': clean_html(json_data.get('description')),
            'thumbnail': json_data.get('thumbnail') or json_data.get('poster'),
            'duration': duration,
            'timestamp': parse_iso8601(json_data.get('published_at')),
            'uploader_id': json_data.get('account_id'),
            'formats': formats,
            'subtitles': subtitles,
            'tags': json_data.get('tags', []),
            'is_live': is_live,
        }