def process_format_stream(fmt_stream, proto, missing_pot, super_resolution=False):
                itag = str_or_none(fmt_stream.get('itag'))
                audio_track = fmt_stream.get('audioTrack') or {}
                quality = fmt_stream.get('quality')
                height = int_or_none(fmt_stream.get('height'))
                if quality == 'tiny' or not quality:
                    quality = fmt_stream.get('audioQuality', '').lower() or quality
                # The 3gp format (17) in android client has a quality of "small",
                # but is actually worse than other formats
                if itag == '17':
                    quality = 'tiny'
                if quality:
                    if itag:
                        itag_qualities[itag] = quality
                    if height:
                        res_qualities[height] = quality

                language_code, language_preference = get_language_code_and_preference(fmt_stream)

                has_drm = bool(fmt_stream.get('drmFamilies'))

                if has_drm:
                    msg = f'Some {client_name} client {proto} formats have been skipped as they are DRM protected. '
                    if client_name == 'tv':
                        msg += (
                            f'{"Your account" if self.is_authenticated else "The current session"} may have '
                            f'an experiment that applies DRM to all videos on the tv client. '
                            f'See  https://github.com/yt-dlp/yt-dlp/issues/12563  for more details.'
                        )
                    self.report_warning(msg, video_id, only_once=True)

                tbr = float_or_none(fmt_stream.get('averageBitrate') or fmt_stream.get('bitrate'), 1000)
                format_duration = traverse_obj(fmt_stream, ('approxDurationMs', {float_or_none(scale=1000)}))
                # Some formats may have much smaller duration than others (possibly damaged during encoding)
                # E.g. 2-nOtRESiUc Ref: https://github.com/yt-dlp/yt-dlp/issues/2823
                # Make sure to avoid false positives with small duration differences.
                # E.g. __2ABJjxzNo, ySuUZEjARPY
                is_damaged = try_call(lambda: format_duration < duration // 2)
                if is_damaged:
                    self.report_warning(
                        f'Some {client_name} client {proto} formats are possibly damaged. They will be deprioritized', video_id, only_once=True)

                if missing_pot and 'missing_pot' not in self._configuration_arg('formats'):
                    self._report_pot_format_skipped(video_id, client_name, proto)
                    return None

                name = fmt_stream.get('qualityLabel') or quality.replace('audio_quality_', '') or ''
                fps = int_or_none(fmt_stream.get('fps')) or 0
                dct = {
                    'asr': int_or_none(fmt_stream.get('audioSampleRate')),
                    'filesize': int_or_none(fmt_stream.get('contentLength')),
                    'format_id': join_nonempty(itag, (
                        'drc' if fmt_stream.get('isDrc')
                        else 'sr' if super_resolution
                        else None)),
                    'format_note': join_nonempty(
                        join_nonempty(audio_track.get('displayName'), audio_track.get('audioIsDefault') and '(default)', delim=' '),
                        name, fmt_stream.get('isDrc') and 'DRC', super_resolution and 'AI-upscaled',
                        try_get(fmt_stream, lambda x: x['projectionType'].replace('RECTANGULAR', '').lower()),
                        try_get(fmt_stream, lambda x: x['spatialAudioType'].replace('SPATIAL_AUDIO_TYPE_', '').lower()),
                        is_damaged and 'DAMAGED', missing_pot and 'MISSING POT',
                        (self.get_param('verbose') or all_formats) and short_client_name(client_name),
                        delim=', '),
                    # Format 22 is likely to be damaged. See https://github.com/yt-dlp/yt-dlp/issues/3372
                    'source_preference': (-5 if itag == '22' else -1) + (100 if 'Premium' in name else 0),
                    'fps': fps if fps > 1 else None,  # For some formats, fps is wrongly returned as 1
                    'audio_channels': fmt_stream.get('audioChannels'),
                    'height': height,
                    'quality': q(quality) - bool(fmt_stream.get('isDrc')) / 2,
                    'has_drm': has_drm,
                    'tbr': tbr,
                    'filesize_approx': filesize_from_tbr(tbr, format_duration),
                    'width': int_or_none(fmt_stream.get('width')),
                    'language': language_code,
                    'language_preference': language_preference,
                    # Strictly de-prioritize damaged and 3gp formats
                    'preference': -10 if is_damaged else -2 if itag == '17' else None,
                }
                mime_mobj = re.match(
                    r'((?:[^/]+)/(?:[^;]+))(?:;\s*codecs="([^"]+)")?', fmt_stream.get('mimeType') or '')
                if mime_mobj:
                    dct['ext'] = mimetype2ext(mime_mobj.group(1))
                    dct.update(parse_codecs(mime_mobj.group(2)))

                single_stream = 'none' in (dct.get('acodec'), dct.get('vcodec'))
                if single_stream and dct.get('ext'):
                    dct['container'] = dct['ext'] + '_dash'

                return dct