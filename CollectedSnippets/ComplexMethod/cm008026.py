def process_info(self, info_dict):
        """Process a single resolved IE result. (Modifies it in-place)"""

        assert info_dict.get('_type', 'video') == 'video'
        original_infodict = info_dict

        if 'format' not in info_dict and 'ext' in info_dict:
            info_dict['format'] = info_dict['ext']

        if self._match_entry(info_dict) is not None:
            info_dict['__write_download_archive'] = 'ignore'
            return

        # Does nothing under normal operation - for backward compatibility of process_info
        self.post_extract(info_dict)

        def replace_info_dict(new_info):
            nonlocal info_dict
            if new_info == info_dict:
                return
            info_dict.clear()
            info_dict.update(new_info)

        new_info, _ = self.pre_process(info_dict, 'video')
        replace_info_dict(new_info)
        self._num_downloads += 1

        # info_dict['_filename'] needs to be set for backward compatibility
        info_dict['_filename'] = full_filename = self.prepare_filename(info_dict, warn=True)
        temp_filename = self.prepare_filename(info_dict, 'temp')
        files_to_move = {}

        # Forced printings
        self.__forced_printings(info_dict, full_filename, incomplete=('format' not in info_dict))

        def check_max_downloads():
            if self._num_downloads >= float(self.params.get('max_downloads') or 'inf'):
                raise MaxDownloadsReached

        if self.params.get('simulate'):
            info_dict['__write_download_archive'] = self.params.get('force_write_download_archive')
            check_max_downloads()
            return

        if full_filename is None:
            return
        if not self._ensure_dir_exists(full_filename):
            return
        if not self._ensure_dir_exists(temp_filename):
            return

        if self._write_description('video', info_dict,
                                   self.prepare_filename(info_dict, 'description')) is None:
            return

        sub_files = self._write_subtitles(info_dict, temp_filename)
        if sub_files is None:
            return
        files_to_move.update(dict(sub_files))

        thumb_files = self._write_thumbnails(
            'video', info_dict, temp_filename, self.prepare_filename(info_dict, 'thumbnail'))
        if thumb_files is None:
            return
        files_to_move.update(dict(thumb_files))

        infofn = self.prepare_filename(info_dict, 'infojson')
        _infojson_written = self._write_info_json('video', info_dict, infofn)
        if _infojson_written:
            info_dict['infojson_filename'] = infofn
            # For backward compatibility, even though it was a private field
            info_dict['__infojson_filename'] = infofn
        elif _infojson_written is None:
            return

        # Write internet shortcut files
        def _write_link_file(link_type):
            url = try_get(info_dict['webpage_url'], iri_to_uri)
            if not url:
                self.report_warning(
                    f'Cannot write internet shortcut file because the actual URL of "{info_dict["webpage_url"]}" is unknown')
                return True
            linkfn = replace_extension(self.prepare_filename(info_dict, 'link'), link_type, info_dict.get('ext'))
            if not self._ensure_dir_exists(linkfn):
                return False
            if self.params.get('overwrites', True) and os.path.exists(linkfn):
                self.to_screen(f'[info] Internet shortcut (.{link_type}) is already present')
                return True
            try:
                self.to_screen(f'[info] Writing internet shortcut (.{link_type}) to: {linkfn}')
                with open(to_high_limit_path(linkfn), 'w', encoding='utf-8',
                          newline='\r\n' if link_type == 'url' else '\n') as linkfile:
                    template_vars = {'url': url}
                    if link_type == 'desktop':
                        template_vars['filename'] = linkfn[:-(len(link_type) + 1)]
                    linkfile.write(LINK_TEMPLATES[link_type] % template_vars)
            except OSError:
                self.report_error(f'Cannot write internet shortcut {linkfn}')
                return False
            return True

        write_links = {
            'url': self.params.get('writeurllink'),
            'webloc': self.params.get('writewebloclink'),
            'desktop': self.params.get('writedesktoplink'),
        }
        if self.params.get('writelink'):
            link_type = ('webloc' if sys.platform == 'darwin'
                         else 'desktop' if sys.platform.startswith('linux')
                         else 'url')
            write_links[link_type] = True

        if any(should_write and not _write_link_file(link_type)
               for link_type, should_write in write_links.items()):
            return

        new_info, files_to_move = self.pre_process(info_dict, 'before_dl', files_to_move)
        replace_info_dict(new_info)

        if self.params.get('skip_download'):
            info_dict['filepath'] = temp_filename
            info_dict['__finaldir'] = os.path.dirname(os.path.abspath(full_filename))
            info_dict['__files_to_move'] = files_to_move
            replace_info_dict(self.run_pp(MoveFilesAfterDownloadPP(self, False), info_dict))
            info_dict['__write_download_archive'] = self.params.get('force_write_download_archive')
        else:
            # Download
            info_dict.setdefault('__postprocessors', [])
            try:

                def existing_video_file(*filepaths):
                    ext = info_dict.get('ext')
                    converted = lambda file: replace_extension(file, self.params.get('final_ext') or ext, ext)
                    file = self.existing_file(itertools.chain(*zip(map(converted, filepaths), filepaths, strict=True)),
                                              default_overwrite=False)
                    if file:
                        info_dict['ext'] = os.path.splitext(file)[1][1:]
                    return file

                fd, success = None, True
                if info_dict.get('protocol') or info_dict.get('url'):
                    fd = get_suitable_downloader(info_dict, self.params, to_stdout=temp_filename == '-')
                    if fd != FFmpegFD and 'no-direct-merge' not in self.params['compat_opts'] and (
                            info_dict.get('section_start') or info_dict.get('section_end')):
                        msg = ('This format cannot be partially downloaded' if FFmpegFD.available()
                               else 'You have requested downloading the video partially, but ffmpeg is not installed')
                        self.report_error(f'{msg}. Aborting')
                        return

                if info_dict.get('requested_formats') is not None:
                    old_ext = info_dict['ext']
                    if self.params.get('merge_output_format') is None:
                        if (info_dict['ext'] == 'webm'
                                and info_dict.get('thumbnails')
                                # check with type instead of pp_key, __name__, or isinstance
                                # since we dont want any custom PPs to trigger this
                                and any(type(pp) == EmbedThumbnailPP for pp in self._pps['post_process'])):  # noqa: E721
                            info_dict['ext'] = 'mkv'
                            self.report_warning(
                                'webm doesn\'t support embedding a thumbnail, mkv will be used')
                    new_ext = info_dict['ext']

                    def correct_ext(filename, ext=new_ext):
                        if filename == '-':
                            return filename
                        filename_real_ext = os.path.splitext(filename)[1][1:]
                        filename_wo_ext = (
                            os.path.splitext(filename)[0]
                            if filename_real_ext in (old_ext, new_ext)
                            else filename)
                        return f'{filename_wo_ext}.{ext}'

                    # Ensure filename always has a correct extension for successful merge
                    full_filename = correct_ext(full_filename)
                    temp_filename = correct_ext(temp_filename)
                    dl_filename = existing_video_file(full_filename, temp_filename)

                    info_dict['__real_download'] = False
                    # NOTE: Copy so that original format dicts are not modified
                    info_dict['requested_formats'] = list(map(dict, info_dict['requested_formats']))

                    merger = FFmpegMergerPP(self)
                    downloaded = []
                    if dl_filename is not None:
                        self.report_file_already_downloaded(dl_filename)
                    elif fd:
                        if fd != FFmpegFD and temp_filename != '-':
                            for f in info_dict['requested_formats']:
                                f['filepath'] = fname = prepend_extension(
                                    correct_ext(temp_filename, info_dict['ext']),
                                    'f{}'.format(f['format_id']), info_dict['ext'])
                                downloaded.append(fname)
                        info_dict['url'] = '\n'.join(f['url'] for f in info_dict['requested_formats'])
                        success, real_download = self.dl(temp_filename, info_dict)
                        info_dict['__real_download'] = real_download
                    else:
                        if self.params.get('allow_unplayable_formats'):
                            self.report_warning(
                                'You have requested merging of multiple formats '
                                'while also allowing unplayable formats to be downloaded. '
                                'The formats won\'t be merged to prevent data corruption.')
                        elif not merger.available:
                            msg = 'You have requested merging of multiple formats but ffmpeg is not installed'
                            if not self.params.get('ignoreerrors'):
                                self.report_error(f'{msg}. Aborting due to --abort-on-error')
                                return
                            self.report_warning(f'{msg}. The formats won\'t be merged')

                        if temp_filename == '-':
                            reason = ('using a downloader other than ffmpeg' if FFmpegFD.can_merge_formats(info_dict, self.params)
                                      else 'but the formats are incompatible for simultaneous download' if merger.available
                                      else 'but ffmpeg is not installed')
                            self.report_warning(
                                f'You have requested downloading multiple formats to stdout {reason}. '
                                'The formats will be streamed one after the other')
                            fname = temp_filename
                        for f in info_dict['requested_formats']:
                            new_info = dict(info_dict)
                            del new_info['requested_formats']
                            new_info.update(f)
                            if temp_filename != '-':
                                fname = prepend_extension(
                                    correct_ext(temp_filename, new_info['ext']),
                                    'f{}'.format(f['format_id']), new_info['ext'])
                                if not self._ensure_dir_exists(fname):
                                    return
                                f['filepath'] = fname
                                downloaded.append(fname)
                            partial_success, real_download = self.dl(fname, new_info)
                            info_dict['__real_download'] = info_dict['__real_download'] or real_download
                            success = success and partial_success

                    if downloaded and merger.available and not self.params.get('allow_unplayable_formats'):
                        info_dict['__postprocessors'].append(merger)
                        info_dict['__files_to_merge'] = downloaded
                        # Even if there were no downloads, it is being merged only now
                        info_dict['__real_download'] = True
                    else:
                        for file in downloaded:
                            files_to_move[file] = None
                else:
                    # Just a single file
                    dl_filename = existing_video_file(full_filename, temp_filename)
                    if dl_filename is None or dl_filename == temp_filename:
                        # dl_filename == temp_filename could mean that the file was partially downloaded with --no-part.
                        # So we should try to resume the download
                        success, real_download = self.dl(temp_filename, info_dict)
                        info_dict['__real_download'] = real_download
                    else:
                        self.report_file_already_downloaded(dl_filename)

                dl_filename = dl_filename or temp_filename
                info_dict['__finaldir'] = os.path.dirname(os.path.abspath(full_filename))

            except network_exceptions as err:
                self.report_error(f'unable to download video data: {err}')
                return
            except OSError as err:
                raise UnavailableVideoError(err)
            except ContentTooShortError as err:
                self.report_error(f'content too short (expected {err.expected} bytes and served {err.downloaded})')
                return

            self._raise_pending_errors(info_dict)
            if success and full_filename != '-':

                def fixup():
                    do_fixup = True
                    fixup_policy = self.params.get('fixup')
                    vid = info_dict['id']

                    if fixup_policy in ('ignore', 'never'):
                        return
                    elif fixup_policy == 'warn':
                        do_fixup = 'warn'
                    elif fixup_policy != 'force':
                        assert fixup_policy in ('detect_or_warn', None)
                        if not info_dict.get('__real_download'):
                            do_fixup = False

                    def ffmpeg_fixup(cndn, msg, cls):
                        if not (do_fixup and cndn):
                            return
                        elif do_fixup == 'warn':
                            self.report_warning(f'{vid}: {msg}')
                            return
                        pp = cls(self)
                        if pp.available:
                            info_dict['__postprocessors'].append(pp)
                        else:
                            self.report_warning(f'{vid}: {msg}. Install ffmpeg to fix this automatically')

                    stretched_ratio = info_dict.get('stretched_ratio')
                    ffmpeg_fixup(stretched_ratio not in (1, None),
                                 f'Non-uniform pixel ratio {stretched_ratio}',
                                 FFmpegFixupStretchedPP)

                    downloader = get_suitable_downloader(info_dict, self.params) if 'protocol' in info_dict else None
                    downloader = downloader.FD_NAME if downloader else None

                    ext = info_dict.get('ext')
                    postprocessed_by_ffmpeg = info_dict.get('requested_formats') or any((
                        isinstance(pp, FFmpegVideoConvertorPP)
                        and resolve_recode_mapping(ext, pp.mapping)[0] not in (ext, None)
                    ) for pp in self._pps['post_process'])

                    if not postprocessed_by_ffmpeg:
                        ffmpeg_fixup(fd != FFmpegFD and ext == 'm4a'
                                     and info_dict.get('container') == 'm4a_dash',
                                     'writing DASH m4a. Only some players support this container',
                                     FFmpegFixupM4aPP)
                        ffmpeg_fixup((downloader == 'hlsnative' and not self.params.get('hls_use_mpegts'))
                                     or (info_dict.get('is_live') and self.params.get('hls_use_mpegts') is None),
                                     'Possible MPEG-TS in MP4 container or malformed AAC timestamps',
                                     FFmpegFixupM3u8PP)
                        ffmpeg_fixup(downloader == 'dashsegments'
                                     and (info_dict.get('is_live') or info_dict.get('is_dash_periods')),
                                     'Possible duplicate MOOV atoms', FFmpegFixupDuplicateMoovPP)

                    ffmpeg_fixup(downloader == 'web_socket_fragment', 'Malformed timestamps detected', FFmpegFixupTimestampPP)
                    ffmpeg_fixup(downloader == 'web_socket_fragment', 'Malformed duration detected', FFmpegFixupDurationPP)

                fixup()
                try:
                    replace_info_dict(self.post_process(dl_filename, info_dict, files_to_move))
                except PostProcessingError as err:
                    self.report_error(f'Postprocessing: {err}')
                    return
                try:
                    for ph in self._post_hooks:
                        ph(info_dict['filepath'])
                except Exception as err:
                    self.report_error(f'post hooks: {err}')
                    return
                info_dict['__write_download_archive'] = True

        assert info_dict is original_infodict  # Make sure the info_dict was modified in-place
        if self.params.get('force_write_download_archive'):
            info_dict['__write_download_archive'] = True
        check_max_downloads()