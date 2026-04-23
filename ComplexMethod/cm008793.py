def _call_downloader(self, tmpfilename, info_dict):
        ffpp = FFmpegPostProcessor(downloader=self)
        if not ffpp.available:
            self.report_error('m3u8 download detected but ffmpeg could not be found. Please install')
            return False
        ffpp.check_version()

        args = [ffpp.executable, '-y']

        for log_level in ('quiet', 'verbose'):
            if self.params.get(log_level, False):
                args += ['-loglevel', log_level]
                break
        if not self.params.get('verbose'):
            args += ['-hide_banner']

        env = None
        proxy = self.params.get('proxy')
        if proxy:
            if not re.match(r'[\da-zA-Z]+://', proxy):
                proxy = f'http://{proxy}'

            if proxy.startswith('socks'):
                self.report_warning(
                    f'{self.get_basename()} does not support SOCKS proxies. Downloading is likely to fail. '
                    'Consider adding --hls-prefer-native to your command.')

            # Since December 2015 ffmpeg supports -http_proxy option (see
            # http://git.videolan.org/?p=ffmpeg.git;a=commit;h=b4eb1f29ebddd60c41a2eb39f5af701e38e0d3fd)
            # We could switch to the following code if we are able to detect version properly
            # args += ['-http_proxy', proxy]
            env = os.environ.copy()
            env['HTTP_PROXY'] = proxy
            env['http_proxy'] = proxy

        start_time, end_time = info_dict.get('section_start') or 0, info_dict.get('section_end')

        fallback_input_args = traverse_obj(info_dict, ('downloader_options', 'ffmpeg_args', ...))

        selected_formats = info_dict.get('requested_formats') or [info_dict]
        for i, fmt in enumerate(selected_formats):
            is_http = re.match(r'https?://', fmt['url'])
            cookies = self.ydl.cookiejar.get_cookies_for_url(fmt['url']) if is_http else []
            if cookies:
                args.extend(['-cookies', ''.join(
                    f'{cookie.name}={cookie.value}; path={cookie.path}; domain={cookie.domain};\r\n'
                    for cookie in cookies)])
            if fmt.get('http_headers') and is_http:
                # Trailing \r\n after each HTTP header is important to prevent warning from ffmpeg:
                # [http @ 00000000003d2fa0] No trailing CRLF found in HTTP header.
                args.extend(['-headers', ''.join(f'{key}: {val}\r\n' for key, val in fmt['http_headers'].items())])

            if start_time:
                args += ['-ss', str(start_time)]
            if end_time:
                args += ['-t', str(end_time - start_time)]

            protocol = fmt.get('protocol')

            if protocol == 'rtmp':
                player_url = fmt.get('player_url')
                page_url = fmt.get('page_url')
                app = fmt.get('app')
                play_path = fmt.get('play_path')
                tc_url = fmt.get('tc_url')
                flash_version = fmt.get('flash_version')
                live = fmt.get('rtmp_live', False)
                conn = fmt.get('rtmp_conn')
                if player_url is not None:
                    args += ['-rtmp_swfverify', player_url]
                if page_url is not None:
                    args += ['-rtmp_pageurl', page_url]
                if app is not None:
                    args += ['-rtmp_app', app]
                if play_path is not None:
                    args += ['-rtmp_playpath', play_path]
                if tc_url is not None:
                    args += ['-rtmp_tcurl', tc_url]
                if flash_version is not None:
                    args += ['-rtmp_flashver', flash_version]
                if live:
                    args += ['-rtmp_live', 'live']
                if isinstance(conn, list):
                    for entry in conn:
                        args += ['-rtmp_conn', entry]
                elif isinstance(conn, str):
                    args += ['-rtmp_conn', conn]

            elif protocol == 'http_dash_segments' and info_dict.get('is_live'):
                # ffmpeg may try to read past the latest available segments for
                # live DASH streams unless we pass `-re`. In modern ffmpeg, this
                # is an alias of `-readrate 1`, but `-readrate` was not added
                # until ffmpeg 5.0, so we must stick to using `-re`
                args += ['-re']

            url = fmt['url']
            if self.params.get('enable_file_urls') and url.startswith('file:'):
                # The default protocol_whitelist is 'file,crypto,data' when reading local m3u8 URLs,
                # so only local segments can be read unless we also include 'http,https,tcp,tls'
                args += ['-protocol_whitelist', 'file,crypto,data,http,https,tcp,tls']
                # ffmpeg incorrectly handles 'file:' URLs by only removing the
                # 'file:' prefix and treating the rest as if it's a normal filepath.
                # FFmpegPostProcessor also depends on this behavior, so we need to fixup the URLs:
                # - On Windows/Cygwin, replace 'file:///' and 'file://localhost/' with 'file:'
                # - On *nix, replace 'file://localhost/' with 'file:/'
                # Ref: https://github.com/yt-dlp/yt-dlp/issues/13781
                #      https://trac.ffmpeg.org/ticket/2702
                url = re.sub(r'^file://(?:localhost)?/', 'file:' if os.name == 'nt' else 'file:/', url)

            args += traverse_obj(fmt, ('downloader_options', 'ffmpeg_args', ...)) or fallback_input_args
            args += [*self._configuration_args((f'_i{i + 1}', '_i')), '-i', url]

        if not (start_time or end_time) or not self.params.get('force_keyframes_at_cuts'):
            args += ['-c', 'copy']

        if info_dict.get('requested_formats') or protocol == 'http_dash_segments':
            for i, fmt in enumerate(selected_formats):
                stream_number = fmt.get('manifest_stream_number', 0)
                args.extend(['-map', f'{i}:{stream_number}'])

        if self.params.get('test', False):
            args += ['-fs', str(self._TEST_FILE_SIZE)]

        ext = info_dict['ext']
        if protocol in ('m3u8', 'm3u8_native'):
            use_mpegts = (tmpfilename == '-') or self.params.get('hls_use_mpegts')
            if use_mpegts is None:
                use_mpegts = info_dict.get('is_live')
            if use_mpegts:
                args += ['-f', 'mpegts']
            else:
                args += ['-f', 'mp4']
                if (ffpp.basename == 'ffmpeg' and ffpp._features.get('needs_adtstoasc')) and (not info_dict.get('acodec') or info_dict['acodec'].split('.')[0] in ('aac', 'mp4a')):
                    args += ['-bsf:a', 'aac_adtstoasc']
        elif protocol == 'rtmp':
            args += ['-f', 'flv']
        elif ext == 'mp4' and tmpfilename == '-':
            args += ['-f', 'mpegts']
        elif ext == 'unknown_video':
            ext = determine_ext(remove_end(tmpfilename, '.part'))
            if ext == 'unknown_video':
                self.report_warning(
                    'The video format is unknown and cannot be downloaded by ffmpeg. '
                    'Explicitly set the extension in the filename to attempt download in that format')
            else:
                self.report_warning(f'The video format is unknown. Trying to download as {ext} according to the filename')
                args += ['-f', EXT_TO_OUT_FORMATS.get(ext, ext)]
        else:
            args += ['-f', EXT_TO_OUT_FORMATS.get(ext, ext)]

        args += traverse_obj(info_dict, ('downloader_options', 'ffmpeg_args_out', ...))

        args += self._configuration_args(('_o1', '_o', ''))

        args = [encodeArgument(opt) for opt in args]
        args.append(ffpp._ffmpeg_filename_argument(tmpfilename))
        self._debug_cmd(args)

        piped = any(fmt['url'] in ('-', 'pipe:') for fmt in selected_formats)
        with Popen(args, stdin=subprocess.PIPE, env=env) as proc:
            if piped:
                self.on_process_started(proc, proc.stdin)
            try:
                retval = proc.wait()
            except BaseException as e:
                # subprocces.run would send the SIGKILL signal to ffmpeg and the
                # mp4 file couldn't be played, but if we ask ffmpeg to quit it
                # produces a file that is playable (this is mostly useful for live
                # streams). Note that Windows is not affected and produces playable
                # files (see https://github.com/ytdl-org/youtube-dl/issues/8300).
                if isinstance(e, KeyboardInterrupt) and sys.platform != 'win32' and not piped:
                    proc.communicate_or_kill(b'q')
                else:
                    proc.kill(timeout=None)
                raise
            return retval