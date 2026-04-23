def _extract_ptmd(self, ptmd_urls, video_id, api_token=None, aspect_ratio=None):
        content_id = None
        duration = None
        formats, src_captions = [], []
        seen_urls = set()

        for ptmd_url in variadic(ptmd_urls):
            ptmd_url, smuggled_data = unsmuggle_url(ptmd_url, {})
            # Is it a DGS variant? (*D*eutsche *G*ebärden*s*prache' / German Sign Language)
            is_dgs = smuggled_data.get('vod_media_type') == 'DGS'
            ptmd = self._call_api(ptmd_url, video_id, 'PTMD data', api_token)

            basename = (
                ptmd.get('basename')
                # ptmd_url examples:
                # https://api.zdf.de/tmd/2/android_native_6/vod/ptmd/mediathek/250328_sendung_hsh/3
                # https://tmd.phoenix.de/tmd/2/android_native_6/vod/ptmd/phoenix/221215_phx_spitzbergen
                or self._search_regex(r'/vod/ptmd/[^/?#]+/(\w+)', ptmd_url, 'content ID', default=None))
            # If this is_dgs, then it's from ZDFIE and it only uses content_id for _old_archive_ids,
            # and the old version of the extractor didn't extract DGS variants, so ignore basename
            if not content_id and not is_dgs:
                content_id = basename

            if not duration:
                duration = traverse_obj(ptmd, ('attributes', 'duration', 'value', {float_or_none(scale=1000)}))
            src_captions += traverse_obj(ptmd, ('captions', ..., {dict}))

            for stream in traverse_obj(ptmd, ('priorityList', ..., 'formitaeten', ..., {dict})):
                for quality in traverse_obj(stream, ('qualities', ..., {dict})):
                    for variant in traverse_obj(quality, ('audio', 'tracks', lambda _, v: url_or_none(v['uri']))):
                        format_url = variant['uri']
                        if format_url in seen_urls:
                            continue
                        seen_urls.add(format_url)
                        ext = determine_ext(format_url)
                        if ext == 'm3u8':
                            fmts = self._extract_m3u8_formats(
                                format_url, video_id, 'mp4', m3u8_id='hls', fatal=False)
                        elif ext in ('mp4', 'webm'):
                            height = int_or_none(quality.get('highestVerticalResolution'))
                            width = round(aspect_ratio * height) if aspect_ratio and height else None
                            fmts = [{
                                'url': format_url,
                                **parse_codecs(quality.get('mimeCodec')),
                                'height': height,
                                'width': width,
                                'filesize': int_or_none(variant.get('filesize')),
                                'format_id': join_nonempty('http', stream.get('type')),
                                'tbr': int_or_none(self._search_regex(r'_(\d+)k_', format_url, 'tbr', default=None)),
                            }]
                        else:
                            self.report_warning(f'Skipping unsupported extension "{ext}"', video_id=video_id)
                            fmts = []

                        f_class = variant.get('class')
                        for f in fmts:
                            f_lang = ISO639Utils.short2long(
                                (f.get('language') or variant.get('language') or '').lower())
                            is_audio_only = f.get('vcodec') == 'none'
                            formats.append({
                                **f,
                                'format_id': join_nonempty(f['format_id'], is_dgs and 'dgs'),
                                'format_note': join_nonempty(
                                    not is_audio_only and f_class,
                                    is_dgs and 'German Sign Language',
                                    f.get('format_note'), delim=', '),
                                'preference': -2 if is_dgs else -1,
                                'language': f_lang,
                                'language_preference': (
                                    -10 if ((is_audio_only and f.get('format_note') == 'Audiodeskription')
                                            or (not is_audio_only and f_class == 'ad'))
                                    else 10 if f_lang == 'deu' and f_class == 'main'
                                    else 5 if f_lang == 'deu'
                                    else 1 if f_class == 'main'
                                    else -1),
                            })

        return {
            'id': content_id or video_id,
            'duration': duration,
            'formats': formats,
            'subtitles': self._extract_subtitles(src_captions),
        }