def _merge(formats_pair):
            format_1, format_2 = formats_pair

            formats_info = []
            formats_info.extend(format_1.get('requested_formats', (format_1,)))
            formats_info.extend(format_2.get('requested_formats', (format_2,)))

            if not allow_multiple_streams['video'] or not allow_multiple_streams['audio']:
                get_no_more = {'video': False, 'audio': False}
                for (i, fmt_info) in enumerate(formats_info):
                    if fmt_info.get('acodec') == fmt_info.get('vcodec') == 'none':
                        formats_info.pop(i)
                        continue
                    for aud_vid in ['audio', 'video']:
                        if not allow_multiple_streams[aud_vid] and fmt_info.get(aud_vid[0] + 'codec') != 'none':
                            if get_no_more[aud_vid]:
                                formats_info.pop(i)
                                break
                            get_no_more[aud_vid] = True

            if len(formats_info) == 1:
                return formats_info[0]

            video_fmts = [fmt_info for fmt_info in formats_info if fmt_info.get('vcodec') != 'none']
            audio_fmts = [fmt_info for fmt_info in formats_info if fmt_info.get('acodec') != 'none']

            the_only_video = video_fmts[0] if len(video_fmts) == 1 else None
            the_only_audio = audio_fmts[0] if len(audio_fmts) == 1 else None

            output_ext = get_compatible_ext(
                vcodecs=[f.get('vcodec') for f in video_fmts],
                acodecs=[f.get('acodec') for f in audio_fmts],
                vexts=[f['ext'] for f in video_fmts],
                aexts=[f['ext'] for f in audio_fmts],
                preferences=(try_call(lambda: self.params['merge_output_format'].split('/'))
                             or (self.params.get('prefer_free_formats') and ('webm', 'mkv'))))

            filtered = lambda *keys: filter(None, (traverse_obj(fmt, *keys) for fmt in formats_info))

            new_dict = {
                'requested_formats': formats_info,
                'format': '+'.join(filtered('format')),
                'format_id': '+'.join(filtered('format_id')),
                'ext': output_ext,
                'protocol': '+'.join(map(determine_protocol, formats_info)),
                'language': '+'.join(orderedSet(filtered('language'))) or None,
                'format_note': '+'.join(orderedSet(filtered('format_note'))) or None,
                'filesize_approx': sum(filtered('filesize', 'filesize_approx')) or None,
                'tbr': sum(filtered('tbr', 'vbr', 'abr')),
            }

            if the_only_video:
                new_dict.update({
                    'width': the_only_video.get('width'),
                    'height': the_only_video.get('height'),
                    'resolution': the_only_video.get('resolution') or self.format_resolution(the_only_video),
                    'fps': the_only_video.get('fps'),
                    'dynamic_range': the_only_video.get('dynamic_range'),
                    'vcodec': the_only_video.get('vcodec'),
                    'vbr': the_only_video.get('vbr'),
                    'stretched_ratio': the_only_video.get('stretched_ratio'),
                    'aspect_ratio': the_only_video.get('aspect_ratio'),
                })

            if the_only_audio:
                new_dict.update({
                    'acodec': the_only_audio.get('acodec'),
                    'abr': the_only_audio.get('abr'),
                    'asr': the_only_audio.get('asr'),
                    'audio_channels': the_only_audio.get('audio_channels'),
                })

            return new_dict