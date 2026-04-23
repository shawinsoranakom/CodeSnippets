def process_video_result(self, info_dict, download=True):
        assert info_dict.get('_type', 'video') == 'video'
        self._num_videos += 1

        if 'id' not in info_dict:
            raise ExtractorError('Missing "id" field in extractor result', ie=info_dict['extractor'])
        elif not info_dict.get('id'):
            raise ExtractorError('Extractor failed to obtain "id"', ie=info_dict['extractor'])

        def report_force_conversion(field, field_not, conversion):
            self.report_warning(
                f'"{field}" field is not {field_not} - forcing {conversion} conversion, '
                'there is an error in extractor')

        def sanitize_string_field(info, string_field):
            field = info.get(string_field)
            if field is None or isinstance(field, str):
                return
            report_force_conversion(string_field, 'a string', 'string')
            info[string_field] = str(field)

        def sanitize_numeric_fields(info):
            for numeric_field in self._NUMERIC_FIELDS:
                field = info.get(numeric_field)
                if field is None or isinstance(field, (int, float)):
                    continue
                report_force_conversion(numeric_field, 'numeric', 'int')
                info[numeric_field] = int_or_none(field)

        sanitize_string_field(info_dict, 'id')
        sanitize_numeric_fields(info_dict)
        if info_dict.get('section_end') and info_dict.get('section_start') is not None:
            info_dict['duration'] = round(info_dict['section_end'] - info_dict['section_start'], 3)
        if (info_dict.get('duration') or 0) <= 0 and info_dict.pop('duration', None):
            self.report_warning('"duration" field is negative, there is an error in extractor')

        chapters = info_dict.get('chapters') or []
        if chapters and chapters[0].get('start_time'):
            chapters.insert(0, {'start_time': 0})

        dummy_chapter = {'end_time': 0, 'start_time': info_dict.get('duration')}
        for idx, (prev, current, next_) in enumerate(zip(
                (dummy_chapter, *chapters), chapters, (*chapters[1:], dummy_chapter), strict=False), 1):
            if current.get('start_time') is None:
                current['start_time'] = prev.get('end_time')
            if not current.get('end_time'):
                current['end_time'] = next_.get('start_time')
            if not current.get('title'):
                current['title'] = f'<Untitled Chapter {idx}>'

        if 'playlist' not in info_dict:
            # It isn't part of a playlist
            info_dict['playlist'] = None
            info_dict['playlist_index'] = None

        self._sanitize_thumbnails(info_dict)

        thumbnail = info_dict.get('thumbnail')
        thumbnails = info_dict.get('thumbnails')
        if thumbnail:
            info_dict['thumbnail'] = sanitize_url(thumbnail)
        elif thumbnails:
            info_dict['thumbnail'] = thumbnails[-1]['url']

        if info_dict.get('display_id') is None and 'id' in info_dict:
            info_dict['display_id'] = info_dict['id']

        self._fill_common_fields(info_dict)

        for cc_kind in ('subtitles', 'automatic_captions'):
            cc = info_dict.get(cc_kind)
            if cc:
                for _, subtitle in cc.items():
                    for subtitle_format in subtitle:
                        if subtitle_format.get('url'):
                            subtitle_format['url'] = sanitize_url(subtitle_format['url'])
                        if subtitle_format.get('ext') is None:
                            subtitle_format['ext'] = determine_ext(subtitle_format['url']).lower()

        automatic_captions = info_dict.get('automatic_captions')
        subtitles = info_dict.get('subtitles')

        info_dict['requested_subtitles'] = self.process_subtitles(
            info_dict['id'], subtitles, automatic_captions)

        formats = self._get_formats(info_dict)

        # Backward compatibility with InfoExtractor._sort_formats
        field_preference = (formats or [{}])[0].pop('__sort_fields', None)
        if field_preference:
            info_dict['_format_sort_fields'] = field_preference

        info_dict['_has_drm'] = any(  # or None ensures --clean-infojson removes it
            f.get('has_drm') and f['has_drm'] != 'maybe' for f in formats) or None
        if not self.params.get('allow_unplayable_formats'):
            formats = [f for f in formats if not f.get('has_drm') or f['has_drm'] == 'maybe']

        if formats and all(f.get('acodec') == f.get('vcodec') == 'none' for f in formats):
            self.report_warning(
                f'{"This video is DRM protected and " if info_dict["_has_drm"] else ""}'
                'only images are available for download. Use --list-formats to see them'.capitalize())

        get_from_start = not info_dict.get('is_live') or bool(self.params.get('live_from_start'))
        if not get_from_start:
            info_dict['title'] += ' ' + dt.datetime.now().strftime('%Y-%m-%d %H:%M')
        if info_dict.get('is_live') and formats:
            formats = [f for f in formats if bool(f.get('is_from_start')) == get_from_start]
            if get_from_start and not formats:
                self.raise_no_formats(info_dict, msg=(
                    '--live-from-start is passed, but there are no formats that can be downloaded from the start. '
                    'If you want to download from the current time, use --no-live-from-start'))

        def is_wellformed(f):
            url = f.get('url')
            if not url:
                self.report_warning(
                    '"url" field is missing or empty - skipping format, '
                    'there is an error in extractor')
                return False
            if isinstance(url, bytes):
                sanitize_string_field(f, 'url')
            return True

        # Filter out malformed formats for better extraction robustness
        formats = list(filter(is_wellformed, formats or []))

        if not formats:
            self.raise_no_formats(info_dict)

        for fmt in formats:
            sanitize_string_field(fmt, 'format_id')
            sanitize_numeric_fields(fmt)
            fmt['url'] = sanitize_url(fmt['url'])
            FormatSorter._fill_sorting_fields(fmt)
            if fmt['ext'] in ('aac', 'opus', 'mp3', 'flac', 'vorbis'):
                if fmt.get('acodec') is None:
                    fmt['acodec'] = fmt['ext']
            if fmt.get('resolution') is None:
                fmt['resolution'] = self.format_resolution(fmt, default=None)
            if fmt.get('dynamic_range') is None and fmt.get('vcodec') != 'none':
                fmt['dynamic_range'] = 'SDR'
            if fmt.get('aspect_ratio') is None:
                fmt['aspect_ratio'] = try_call(lambda: round(fmt['width'] / fmt['height'], 2))
            # For fragmented formats, "tbr" is often max bitrate and not average
            if (('manifest-filesize-approx' in self.params['compat_opts'] or not fmt.get('manifest_url'))
                    and not fmt.get('filesize') and not fmt.get('filesize_approx')):
                fmt['filesize_approx'] = filesize_from_tbr(fmt.get('tbr'), info_dict.get('duration'))
            fmt['http_headers'] = self._calc_headers(collections.ChainMap(fmt, info_dict), load_cookies=True)

        # Safeguard against old/insecure infojson when using --load-info-json
        if info_dict.get('http_headers'):
            info_dict['http_headers'] = HTTPHeaderDict(info_dict['http_headers'])
            info_dict['http_headers'].pop('Cookie', None)

        # This is copied to http_headers by the above _calc_headers and can now be removed
        if '__x_forwarded_for_ip' in info_dict:
            del info_dict['__x_forwarded_for_ip']

        self.sort_formats({
            'formats': formats,
            '_format_sort_fields': info_dict.get('_format_sort_fields'),
        })

        # Sanitize and group by format_id
        formats_dict = {}
        for i, fmt in enumerate(formats):
            if not fmt.get('format_id'):
                fmt['format_id'] = str(i)
            else:
                # Sanitize format_id from characters used in format selector expression
                fmt['format_id'] = re.sub(r'[\s,/+\[\]()]', '_', fmt['format_id'])
            formats_dict.setdefault(fmt['format_id'], []).append(fmt)

        # Make sure all formats have unique format_id
        common_exts = set(itertools.chain(*self._format_selection_exts.values()))
        for format_id, ambiguous_formats in formats_dict.items():
            ambigious_id = len(ambiguous_formats) > 1
            for i, fmt in enumerate(ambiguous_formats):
                if ambigious_id:
                    fmt['format_id'] = f'{format_id}-{i}'
                # Ensure there is no conflict between id and ext in format selection
                # See https://github.com/yt-dlp/yt-dlp/issues/1282
                if fmt['format_id'] != fmt['ext'] and fmt['format_id'] in common_exts:
                    fmt['format_id'] = 'f{}'.format(fmt['format_id'])

                if fmt.get('format') is None:
                    fmt['format'] = '{id} - {res}{note}'.format(
                        id=fmt['format_id'],
                        res=self.format_resolution(fmt),
                        note=format_field(fmt, 'format_note', ' (%s)'),
                    )

        if self.params.get('check_formats') is True:
            formats = LazyList(self._check_formats(formats[::-1], warning=False), reverse=True)

        if not formats or formats[0] is not info_dict:
            # only set the 'formats' fields if the original info_dict list them
            # otherwise we end up with a circular reference, the first (and unique)
            # element in the 'formats' field in info_dict is info_dict itself,
            # which can't be exported to json
            info_dict['formats'] = formats

        info_dict, _ = self.pre_process(info_dict)

        if self._match_entry(info_dict, incomplete=self._format_fields) is not None:
            return info_dict

        self.post_extract(info_dict)
        info_dict, _ = self.pre_process(info_dict, 'after_filter')

        # The pre-processors may have modified the formats
        formats = self._get_formats(info_dict)

        list_only = self.params.get('simulate') == 'list_only'
        interactive_format_selection = not list_only and self.format_selector == '-'
        if self.params.get('list_thumbnails'):
            self.list_thumbnails(info_dict)
        if self.params.get('listsubtitles'):
            if 'automatic_captions' in info_dict:
                self.list_subtitles(
                    info_dict['id'], automatic_captions, 'automatic captions')
            self.list_subtitles(info_dict['id'], subtitles, 'subtitles')
        if self.params.get('listformats') or interactive_format_selection:
            self.list_formats(info_dict)
        if list_only:
            # Without this printing, -F --print-json will not work
            self.__forced_printings(info_dict)
            return info_dict

        format_selector = self.format_selector
        while True:
            if interactive_format_selection:
                if not formats:
                    # Bypass interactive format selection if no formats & --ignore-no-formats-error
                    formats_to_download = None
                    break
                self.to_screen(self._format_screen('\nEnter format selector ', self.Styles.EMPHASIS)
                               + '(Press ENTER for default, or Ctrl+C to quit)'
                               + self._format_screen(': ', self.Styles.EMPHASIS), skip_eol=True)
                req_format = input()
                try:
                    format_selector = self.build_format_selector(req_format) if req_format else None
                except SyntaxError as err:
                    self.report_error(err, tb=False, is_error=False)
                    continue

            if format_selector is None:
                req_format = self._default_format_spec(info_dict)
                self.write_debug(f'Default format spec: {req_format}')
                format_selector = self.build_format_selector(req_format)

            formats_to_download = self._select_formats(formats, format_selector)
            if interactive_format_selection and not formats_to_download:
                self.report_error('Requested format is not available', tb=False, is_error=False)
                continue
            break

        if not formats_to_download:
            if not self.params.get('ignore_no_formats_error'):
                raise ExtractorError(
                    'Requested format is not available. Use --list-formats for a list of available formats',
                    expected=True, video_id=info_dict['id'], ie=info_dict['extractor'])
            self.report_warning('Requested format is not available')
            # Process what we can, even without any available formats.
            formats_to_download = [{}]

        requested_ranges = tuple(self.params.get('download_ranges', lambda *_: [{}])(info_dict, self))
        best_format, downloaded_formats = formats_to_download[-1], []
        if download:
            if best_format and requested_ranges:
                def to_screen(*msg):
                    self.to_screen(f'[info] {info_dict["id"]}: {" ".join(", ".join(variadic(m)) for m in msg)}')

                to_screen(f'Downloading {len(formats_to_download)} format(s):',
                          (f['format_id'] for f in formats_to_download))
                if requested_ranges != ({}, ):
                    to_screen(f'Downloading {len(requested_ranges)} time ranges:',
                              (f'{c["start_time"]:.1f}-{c["end_time"]:.1f}' for c in requested_ranges))
            max_downloads_reached = False

            for fmt, chapter in itertools.product(formats_to_download, requested_ranges):
                new_info = self._copy_infodict(info_dict)
                new_info.update(fmt)
                offset, duration = info_dict.get('section_start') or 0, info_dict.get('duration') or float('inf')
                end_time = offset + min(chapter.get('end_time', duration), duration)
                # duration may not be accurate. So allow deviations <1sec
                if end_time == float('inf') or end_time > offset + duration + 1:
                    end_time = None
                if chapter or offset:
                    new_info.update({
                        'section_start': offset + chapter.get('start_time', 0),
                        'section_end': end_time,
                        'section_title': chapter.get('title'),
                        'section_number': chapter.get('index'),
                    })
                downloaded_formats.append(new_info)
                try:
                    self.process_info(new_info)
                except MaxDownloadsReached:
                    max_downloads_reached = True
                self._raise_pending_errors(new_info)
                # Remove copied info
                for key, val in tuple(new_info.items()):
                    if info_dict.get(key) == val:
                        new_info.pop(key)
                if max_downloads_reached:
                    break

            write_archive = {f.get('__write_download_archive', False) for f in downloaded_formats}
            assert write_archive.issubset({True, False, 'ignore'})
            if True in write_archive and False not in write_archive:
                self.record_download_archive(info_dict)

            info_dict['requested_downloads'] = downloaded_formats
            info_dict = self.run_all_pps('after_video', info_dict)
            if max_downloads_reached:
                raise MaxDownloadsReached

        # We update the info dict with the selected best quality format (backwards compatibility)
        info_dict.update(best_format)
        return info_dict