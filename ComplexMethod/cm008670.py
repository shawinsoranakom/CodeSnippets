def _parse_brightcove_metadata(self, json_data, video_id, headers={}):
        formats, subtitles = [], {}
        sources = json_data.get('sources') or []
        for source in sources:
            container = source.get('container')
            ext = mimetype2ext(source.get('type'))
            src = source.get('src')
            if ext == 'm3u8' or container == 'M2TS':
                if not src:
                    continue
                fmts, subs = self._extract_m3u8_formats_and_subtitles(
                    src, video_id, 'mp4', 'm3u8_native', m3u8_id='hls', fatal=False)
                subtitles = self._merge_subtitles(subtitles, subs)
            elif ext == 'mpd':
                if not src:
                    continue
                fmts, subs = self._extract_mpd_formats_and_subtitles(src, video_id, 'dash', fatal=False)
                subtitles = self._merge_subtitles(subtitles, subs)
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
                    return join_nonempty(kind, tbr and f'{int(tbr)}k', height and f'{height}p')

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
                fmts = [f]

            # https://support.brightcove.com/playback-api-video-fields-reference#key_systems_object
            if container == 'WVM' or source.get('key_systems') or ext == 'ism':
                for f in fmts:
                    f['has_drm'] = True
            formats.extend(fmts)

        if not formats:
            errors = json_data.get('errors')
            if errors:
                error = errors[0]
                self.raise_no_formats(
                    error.get('message') or error.get('error_subcode') or error['error_code'], expected=True)

        headers.pop('Authorization', None)  # or else http formats will give error 400
        for f in formats:
            f.setdefault('http_headers', {}).update(headers)

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

        common_res = [(160, 90), (320, 180), (480, 720), (640, 360), (768, 432), (1024, 576), (1280, 720), (1366, 768), (1920, 1080)]
        thumb_base_url = dict_get(json_data, ('poster', 'thumbnail'))
        thumbnails = [{
            'url': re.sub(r'\d+x\d+', f'{w}x{h}', thumb_base_url),
            'width': w,
            'height': h,
        } for w, h in common_res] if thumb_base_url else None

        return {
            'id': video_id,
            'thumbnails': thumbnails,
            'duration': duration,
            'formats': formats,
            'subtitles': subtitles,
            'is_live': is_live,
            **traverse_obj(json_data, {
                'title': ('name', {clean_html}),
                'description': ('description', {clean_html}),
                'tags': ('tags', ..., {str}, filter, all, filter),
                'timestamp': ('published_at', {parse_iso8601}),
                'uploader_id': ('account_id', {str}),
            }),
        }