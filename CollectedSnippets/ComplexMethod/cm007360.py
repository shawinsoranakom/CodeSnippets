def process_info(self, info_dict):
        """Process a single resolved IE result."""

        assert info_dict.get('_type', 'video') == 'video'

        max_downloads = int_or_none(self.params.get('max_downloads')) or float('inf')
        if self._num_downloads >= max_downloads:
            raise MaxDownloadsReached()

        # TODO: backward compatibility, to be removed
        info_dict['fulltitle'] = info_dict['title']

        if 'format' not in info_dict:
            info_dict['format'] = info_dict['ext']

        reason = self._match_entry(info_dict, incomplete=False)
        if reason is not None:
            self.to_screen('[download] ' + reason)
            return

        self._num_downloads += 1

        info_dict['_filename'] = filename = self.prepare_filename(info_dict)

        # Forced printings
        self.__forced_printings(info_dict, filename, incomplete=False)

        # Do nothing else if in simulate mode
        if self.params.get('simulate', False):
            return

        if filename is None:
            return

        def ensure_dir_exists(path):
            try:
                dn = os.path.dirname(path)
                if dn and not os.path.exists(dn):
                    os.makedirs(dn)
                return True
            except (OSError, IOError) as err:
                if isinstance(err, OSError) and err.errno == errno.EEXIST:
                    return True
                self.report_error('unable to create directory ' + error_to_compat_str(err))
                return False

        if not ensure_dir_exists(sanitize_path(encodeFilename(filename))):
            return

        if self.params.get('writedescription', False):
            descfn = replace_extension(filename, 'description', info_dict.get('ext'))
            if self.params.get('nooverwrites', False) and os.path.exists(encodeFilename(descfn)):
                self.to_screen('[info] Video description is already present')
            elif info_dict.get('description') is None:
                self.report_warning('There\'s no description to write.')
            else:
                try:
                    self.to_screen('[info] Writing video description to: ' + descfn)
                    with open(encodeFilename(descfn), 'w', encoding='utf-8') as descfile:
                        descfile.write(info_dict['description'])
                except (OSError, IOError):
                    self.report_error('Cannot write description file ' + descfn)
                    return

        if self.params.get('writeannotations', False):
            annofn = replace_extension(filename, 'annotations.xml', info_dict.get('ext'))
            if self.params.get('nooverwrites', False) and os.path.exists(encodeFilename(annofn)):
                self.to_screen('[info] Video annotations are already present')
            elif not info_dict.get('annotations'):
                self.report_warning('There are no annotations to write.')
            else:
                try:
                    self.to_screen('[info] Writing video annotations to: ' + annofn)
                    with open(encodeFilename(annofn), 'w', encoding='utf-8') as annofile:
                        annofile.write(info_dict['annotations'])
                except (KeyError, TypeError):
                    self.report_warning('There are no annotations to write.')
                except (OSError, IOError):
                    self.report_error('Cannot write annotations file: ' + annofn)
                    return

        subtitles_are_requested = any([self.params.get('writesubtitles', False),
                                       self.params.get('writeautomaticsub')])

        if subtitles_are_requested and info_dict.get('requested_subtitles'):
            # subtitles download errors are already managed as troubles in relevant IE
            # that way it will silently go on when used with unsupporting IE
            subtitles = info_dict['requested_subtitles']
            ie = self.get_info_extractor(info_dict['extractor_key'])
            for sub_lang, sub_info in subtitles.items():
                sub_format = sub_info['ext']
                sub_filename = subtitles_filename(filename, sub_lang, sub_format, info_dict.get('ext'))
                if self.params.get('nooverwrites', False) and os.path.exists(encodeFilename(sub_filename)):
                    self.to_screen('[info] Video subtitle %s.%s is already present' % (sub_lang, sub_format))
                else:
                    self.to_screen('[info] Writing video subtitles to: ' + sub_filename)
                    if sub_info.get('data') is not None:
                        try:
                            # Use newline='' to prevent conversion of newline characters
                            # See https://github.com/ytdl-org/youtube-dl/issues/10268
                            with open(encodeFilename(sub_filename), 'w', encoding='utf-8', newline='') as subfile:
                                subfile.write(sub_info['data'])
                        except (OSError, IOError):
                            self.report_error('Cannot write subtitles file ' + sub_filename)
                            return
                    else:
                        try:
                            sub_data = ie._request_webpage(
                                sub_info['url'], info_dict['id'], note=False).read()
                            with open(encodeFilename(sub_filename), 'wb') as subfile:
                                subfile.write(sub_data)
                        except (ExtractorError, IOError, OSError, ValueError) as err:
                            self.report_warning('Unable to download subtitle for "%s": %s' %
                                                (sub_lang, error_to_compat_str(err)))
                            continue

        self._write_info_json(
            'video description', info_dict,
            replace_extension(filename, 'info.json', info_dict.get('ext')))

        self._write_thumbnails(info_dict, filename)

        if not self.params.get('skip_download', False):
            try:
                def checked_get_suitable_downloader(info_dict, params):
                    ed_args = params.get('external_downloader_args')
                    dler = get_suitable_downloader(info_dict, params)
                    if ed_args and not params.get('external_downloader_args'):
                        # external_downloader_args was cleared because external_downloader was rejected
                        self.report_warning('Requested external downloader cannot be used: '
                                            'ignoring --external-downloader-args.')
                    return dler

                def dl(name, info):
                    fd = checked_get_suitable_downloader(info, self.params)(self, self.params)
                    for ph in self._progress_hooks:
                        fd.add_progress_hook(ph)
                    if self.params.get('verbose'):
                        self.to_screen('[debug] Invoking downloader on %r' % info.get('url'))

                    new_info = dict((k, v) for k, v in info.items() if not k.startswith('__p'))
                    new_info['http_headers'] = self._calc_headers(new_info)

                    return fd.download(name, new_info)

                if info_dict.get('requested_formats') is not None:
                    downloaded = []
                    success = True
                    merger = FFmpegMergerPP(self)
                    if not merger.available:
                        postprocessors = []
                        self.report_warning('You have requested multiple '
                                            'formats but ffmpeg or avconv are not installed.'
                                            ' The formats won\'t be merged.')
                    else:
                        postprocessors = [merger]

                    def compatible_formats(formats):
                        video, audio = formats
                        # Check extension
                        video_ext, audio_ext = video.get('ext'), audio.get('ext')
                        if video_ext and audio_ext:
                            COMPATIBLE_EXTS = (
                                ('mp3', 'mp4', 'm4a', 'm4p', 'm4b', 'm4r', 'm4v', 'ismv', 'isma'),
                                ('webm')
                            )
                            for exts in COMPATIBLE_EXTS:
                                if video_ext in exts and audio_ext in exts:
                                    return True
                        # TODO: Check acodec/vcodec
                        return False

                    exts = [info_dict['ext']]
                    requested_formats = info_dict['requested_formats']
                    if self.params.get('merge_output_format') is None and not compatible_formats(requested_formats):
                        info_dict['ext'] = 'mkv'
                        self.report_warning(
                            'Requested formats are incompatible for merge and will be merged into mkv.')
                    exts.append(info_dict['ext'])

                    # Ensure filename always has a correct extension for successful merge
                    def correct_ext(filename, ext=exts[1]):
                        if filename == '-':
                            return filename
                        f_name, f_real_ext = os.path.splitext(filename)
                        f_real_ext = f_real_ext[1:]
                        filename_wo_ext = f_name if f_real_ext in exts else filename
                        if ext is None:
                            ext = f_real_ext or None
                        return join_nonempty(filename_wo_ext, ext, delim='.')

                    filename = correct_ext(filename)
                    if os.path.exists(encodeFilename(filename)):
                        self.to_screen(
                            '[download] %s has already been downloaded and '
                            'merged' % filename)
                    else:
                        for f in requested_formats:
                            new_info = dict(info_dict)
                            new_info.update(f)
                            fname = prepend_extension(
                                correct_ext(
                                    self.prepare_filename(new_info), new_info['ext']),
                                'f%s' % (f['format_id'],), new_info['ext'])
                            if not ensure_dir_exists(fname):
                                return
                            downloaded.append(fname)
                            partial_success = dl(fname, new_info)
                            success = success and partial_success
                        info_dict['__postprocessors'] = postprocessors
                        info_dict['__files_to_merge'] = downloaded
                else:
                    # Just a single file
                    success = dl(filename, info_dict)
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self.report_error('unable to download video data: %s' % error_to_compat_str(err))
                return
            except (OSError, IOError) as err:
                raise UnavailableVideoError(err)
            except (ContentTooShortError, ) as err:
                self.report_error('content too short (expected %s bytes and served %s)' % (err.expected, err.downloaded))
                return

            if success and filename != '-':
                # Fixup content
                fixup_policy = self.params.get('fixup')
                if fixup_policy is None:
                    fixup_policy = 'detect_or_warn'

                INSTALL_FFMPEG_MESSAGE = 'Install ffmpeg or avconv to fix this automatically.'

                stretched_ratio = info_dict.get('stretched_ratio')
                if stretched_ratio is not None and stretched_ratio != 1:
                    if fixup_policy == 'warn':
                        self.report_warning('%s: Non-uniform pixel ratio (%s)' % (
                            info_dict['id'], stretched_ratio))
                    elif fixup_policy == 'detect_or_warn':
                        stretched_pp = FFmpegFixupStretchedPP(self)
                        if stretched_pp.available:
                            info_dict.setdefault('__postprocessors', [])
                            info_dict['__postprocessors'].append(stretched_pp)
                        else:
                            self.report_warning(
                                '%s: Non-uniform pixel ratio (%s). %s'
                                % (info_dict['id'], stretched_ratio, INSTALL_FFMPEG_MESSAGE))
                    else:
                        assert fixup_policy in ('ignore', 'never')

                if (info_dict.get('requested_formats') is None
                        and info_dict.get('container') == 'm4a_dash'):
                    if fixup_policy == 'warn':
                        self.report_warning(
                            '%s: writing DASH m4a. '
                            'Only some players support this container.'
                            % info_dict['id'])
                    elif fixup_policy == 'detect_or_warn':
                        fixup_pp = FFmpegFixupM4aPP(self)
                        if fixup_pp.available:
                            info_dict.setdefault('__postprocessors', [])
                            info_dict['__postprocessors'].append(fixup_pp)
                        else:
                            self.report_warning(
                                '%s: writing DASH m4a. '
                                'Only some players support this container. %s'
                                % (info_dict['id'], INSTALL_FFMPEG_MESSAGE))
                    else:
                        assert fixup_policy in ('ignore', 'never')

                if (info_dict.get('protocol') == 'm3u8_native'
                        or info_dict.get('protocol') == 'm3u8'
                        and self.params.get('hls_prefer_native')):
                    if fixup_policy == 'warn':
                        self.report_warning('%s: malformed AAC bitstream detected.' % (
                            info_dict['id']))
                    elif fixup_policy == 'detect_or_warn':
                        fixup_pp = FFmpegFixupM3u8PP(self)
                        if fixup_pp.available:
                            info_dict.setdefault('__postprocessors', [])
                            info_dict['__postprocessors'].append(fixup_pp)
                        else:
                            self.report_warning(
                                '%s: malformed AAC bitstream detected. %s'
                                % (info_dict['id'], INSTALL_FFMPEG_MESSAGE))
                    else:
                        assert fixup_policy in ('ignore', 'never')

                try:
                    self.post_process(filename, info_dict)
                except (PostProcessingError) as err:
                    self.report_error('postprocessing: %s' % error_to_compat_str(err))
                    return
                self.record_download_archive(info_dict)
                # avoid possible nugatory search for further items (PR #26638)
                if self._num_downloads >= max_downloads:
                    raise MaxDownloadsReached()