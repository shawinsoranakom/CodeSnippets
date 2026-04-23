def process_video_result(self, info_dict, download=True):
        assert info_dict.get('_type', 'video') == 'video'

        if 'id' not in info_dict:
            raise ExtractorError('Missing "id" field in extractor result')
        if 'title' not in info_dict:
            raise ExtractorError('Missing "title" field in extractor result')

        def report_force_conversion(field, field_not, conversion):
            self.report_warning(
                '"%s" field is not %s - forcing %s conversion, there is an error in extractor'
                % (field, field_not, conversion))

        def sanitize_string_field(info, string_field):
            field = info.get(string_field)
            if field is None or isinstance(field, compat_str):
                return
            report_force_conversion(string_field, 'a string', 'string')
            info[string_field] = compat_str(field)

        def sanitize_numeric_fields(info):
            for numeric_field in self._NUMERIC_FIELDS:
                field = info.get(numeric_field)
                if field is None or isinstance(field, compat_numeric_types):
                    continue
                report_force_conversion(numeric_field, 'numeric', 'int')
                info[numeric_field] = int_or_none(field)

        sanitize_string_field(info_dict, 'id')
        sanitize_numeric_fields(info_dict)

        if 'playlist' not in info_dict:
            # It isn't part of a playlist
            info_dict['playlist'] = None
            info_dict['playlist_index'] = None

        thumbnails = info_dict.get('thumbnails')
        if thumbnails is None:
            thumbnail = info_dict.get('thumbnail')
            if thumbnail:
                info_dict['thumbnails'] = thumbnails = [{'url': thumbnail}]
        if thumbnails:
            thumbnails.sort(key=lambda t: (
                t.get('preference') if t.get('preference') is not None else -1,
                t.get('width') if t.get('width') is not None else -1,
                t.get('height') if t.get('height') is not None else -1,
                t.get('id') if t.get('id') is not None else '', t.get('url')))
            for i, t in enumerate(thumbnails):
                t['url'] = sanitize_url(t['url'])
                if t.get('width') and t.get('height'):
                    t['resolution'] = '%dx%d' % (t['width'], t['height'])
                if t.get('id') is None:
                    t['id'] = '%d' % i

        if self.params.get('list_thumbnails'):
            self.list_thumbnails(info_dict)
            return

        thumbnail = info_dict.get('thumbnail')
        if thumbnail:
            info_dict['thumbnail'] = sanitize_url(thumbnail)
        elif thumbnails:
            info_dict['thumbnail'] = thumbnails[-1]['url']

        if 'display_id' not in info_dict and 'id' in info_dict:
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

        if self.params.get('listsubtitles', False):
            if 'automatic_captions' in info_dict:
                self.list_subtitles(
                    info_dict['id'], automatic_captions, 'automatic captions')
            self.list_subtitles(info_dict['id'], subtitles, 'subtitles')
            return

        info_dict['requested_subtitles'] = self.process_subtitles(
            info_dict['id'], subtitles, automatic_captions)

        # We now pick which formats have to be downloaded
        if info_dict.get('formats') is None:
            # There's only one format available
            formats = [info_dict]
        else:
            formats = info_dict['formats']

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
            raise ExtractorError('No video formats found!')

        formats_dict = {}

        # We check that all the formats have the format and format_id fields
        for i, format in enumerate(formats):
            sanitize_string_field(format, 'format_id')
            sanitize_numeric_fields(format)
            format['url'] = sanitize_url(format['url'])
            if not format.get('format_id'):
                format['format_id'] = compat_str(i)
            else:
                # Sanitize format_id from characters used in format selector expression
                format['format_id'] = re.sub(r'[\s,/+\[\]()]', '_', format['format_id'])
            format_id = format['format_id']
            if format_id not in formats_dict:
                formats_dict[format_id] = []
            formats_dict[format_id].append(format)

        # Make sure all formats have unique format_id
        for format_id, ambiguous_formats in formats_dict.items():
            if len(ambiguous_formats) > 1:
                for i, format in enumerate(ambiguous_formats):
                    format['format_id'] = '%s-%d' % (format_id, i)

        for i, format in enumerate(formats):
            if format.get('format') is None:
                format['format'] = '{id} - {res}{note}'.format(
                    id=format['format_id'],
                    res=self.format_resolution(format),
                    note=' ({0})'.format(format['format_note']) if format.get('format_note') is not None else '',
                )
            # Automatically determine file extension if missing
            if format.get('ext') is None:
                format['ext'] = determine_ext(format['url']).lower()
            # Automatically determine protocol if missing (useful for format
            # selection purposes)
            if format.get('protocol') is None:
                format['protocol'] = determine_protocol(format)
            # Add HTTP headers, so that external programs can use them from the
            # json output
            format['http_headers'] = self._calc_headers(ChainMap(format, info_dict), load_cookies=True)

        # Safeguard against old/insecure infojson when using --load-info-json
        info_dict['http_headers'] = self._remove_cookie_header(
            info_dict.get('http_headers') or {}) or None

        # Remove private housekeeping stuff (copied to http_headers in _calc_headers())
        if '__x_forwarded_for_ip' in info_dict:
            del info_dict['__x_forwarded_for_ip']

        # TODO Central sorting goes here

        if formats[0] is not info_dict:
            # only set the 'formats' fields if the original info_dict list them
            # otherwise we end up with a circular reference, the first (and unique)
            # element in the 'formats' field in info_dict is info_dict itself,
            # which can't be exported to json
            info_dict['formats'] = formats
        if self.params.get('listformats'):
            self.list_formats(info_dict)
            return

        req_format = self.params.get('format')
        if req_format is None:
            req_format = self._default_format_spec(info_dict, download=download)
            if self.params.get('verbose'):
                self._write_string('[debug] Default format spec: %s\n' % req_format)

        format_selector = self.build_format_selector(req_format)

        # While in format selection we may need to have an access to the original
        # format set in order to calculate some metrics or do some processing.
        # For now we need to be able to guess whether original formats provided
        # by extractor are incomplete or not (i.e. whether extractor provides only
        # video-only or audio-only formats) for proper formats selection for
        # extractors with such incomplete formats (see
        # https://github.com/ytdl-org/youtube-dl/pull/5556).
        # Since formats may be filtered during format selection and may not match
        # the original formats the results may be incorrect. Thus original formats
        # or pre-calculated metrics should be passed to format selection routines
        # as well.
        # We will pass a context object containing all necessary additional data
        # instead of just formats.
        # This fixes incorrect format selection issue (see
        # https://github.com/ytdl-org/youtube-dl/issues/10083).
        incomplete_formats = (
            # All formats are video-only or
            all(f.get('vcodec') != 'none' and f.get('acodec') == 'none' for f in formats)
            # all formats are audio-only
            or all(f.get('vcodec') == 'none' and f.get('acodec') != 'none' for f in formats))

        ctx = {
            'formats': formats,
            'incomplete_formats': incomplete_formats,
        }

        formats_to_download = list(format_selector(ctx))
        if not formats_to_download:
            raise ExtractorError('requested format not available',
                                 expected=True)

        if download:
            if len(formats_to_download) > 1:
                self.to_screen('[info] %s: downloading video in %s formats' % (info_dict['id'], len(formats_to_download)))
            for format in formats_to_download:
                new_info = dict(info_dict)
                new_info.update(format)
                self.process_info(new_info)
        # We update the info dict with the best quality format (backwards compatibility)
        info_dict.update(formats_to_download[-1])
        return info_dict