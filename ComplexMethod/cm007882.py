def _call_downloader(self, tmpfilename, info_dict):
        # `downloader` means the parent `YoutubeDL`
        ffpp = FFmpegPostProcessor(downloader=self.ydl)
        if not ffpp.available:
            self.report_error('ffmpeg required for download but no ffmpeg (nor avconv) executable could be found. Please install one.')
            return False
        ffpp.check_version()

        args = [ffpp.executable, '-y']

        for log_level in ('quiet', 'verbose'):
            if self.params.get(log_level, False):
                args += ['-loglevel', log_level]
                break

        seekable = info_dict.get('_seekable')
        if seekable is not None:
            # setting -seekable prevents ffmpeg from guessing if the server
            # supports seeking(by adding the header `Range: bytes=0-`), which
            # can cause problems in some cases
            # https://github.com/ytdl-org/youtube-dl/issues/11800#issuecomment-275037127
            # http://trac.ffmpeg.org/ticket/6125#comment:10
            args += ['-seekable', '1' if seekable else '0']

        args += self._configuration_args()

        # start_time = info_dict.get('start_time') or 0
        # if start_time:
        #     args += ['-ss', compat_str(start_time)]
        # end_time = info_dict.get('end_time')
        # if end_time:
        #     args += ['-t', compat_str(end_time - start_time)]

        url = info_dict['url']
        cookies = self.ydl.cookiejar.get_cookies_for_url(url)
        if cookies:
            args.extend(['-cookies', ''.join(
                '{0}={1}; path={2}; domain={3};\r\n'.format(
                    cookie.name, cookie.value, cookie.path, cookie.domain)
                for cookie in cookies)])

        if info_dict.get('http_headers') and re.match(r'^https?://', url):
            # Trailing \r\n after each HTTP header is important to prevent warning from ffmpeg/avconv:
            # [http @ 00000000003d2fa0] No trailing CRLF found in HTTP header.
            headers = handle_youtubedl_headers(info_dict['http_headers'])
            args += [
                '-headers',
                ''.join('%s: %s\r\n' % (key, val) for key, val in headers.items())]

        env = None
        proxy = self.params.get('proxy')
        if proxy:
            if not re.match(r'^[\da-zA-Z]+://', proxy):
                proxy = 'http://%s' % proxy

            if proxy.startswith('socks'):
                self.report_warning(
                    '%s does not support SOCKS proxies. Downloading is likely to fail. '
                    'Consider adding --hls-prefer-native to your command.' % self.get_basename())

            # Since December 2015 ffmpeg supports -http_proxy option (see
            # http://git.videolan.org/?p=ffmpeg.git;a=commit;h=b4eb1f29ebddd60c41a2eb39f5af701e38e0d3fd)
            # We could switch to the following code if we are able to detect version properly
            # args += ['-http_proxy', proxy]
            env = os.environ.copy()
            compat_setenv('HTTP_PROXY', proxy, env=env)
            compat_setenv('http_proxy', proxy, env=env)

        protocol = info_dict.get('protocol')

        if protocol == 'rtmp':
            player_url = info_dict.get('player_url')
            page_url = info_dict.get('page_url')
            app = info_dict.get('app')
            play_path = info_dict.get('play_path')
            tc_url = info_dict.get('tc_url')
            flash_version = info_dict.get('flash_version')
            live = info_dict.get('rtmp_live', False)
            conn = info_dict.get('rtmp_conn')
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
            elif isinstance(conn, compat_str):
                args += ['-rtmp_conn', conn]

        args += ['-i', url, '-c', 'copy']

        if self.params.get('test', False):
            args += ['-fs', compat_str(self._TEST_FILE_SIZE)]

        if protocol in ('m3u8', 'm3u8_native'):
            if self.params.get('hls_use_mpegts', False) or tmpfilename == '-':
                args += ['-f', 'mpegts']
            else:
                args += ['-f', 'mp4']
                if (ffpp.basename == 'ffmpeg' and is_outdated_version(ffpp._versions['ffmpeg'], '3.2', False)) and (not info_dict.get('acodec') or info_dict['acodec'].split('.')[0] in ('aac', 'mp4a')):
                    args += ['-bsf:a', 'aac_adtstoasc']
        elif protocol == 'rtmp':
            args += ['-f', 'flv']
        else:
            args += ['-f', EXT_TO_OUT_FORMATS.get(info_dict['ext'], info_dict['ext'])]

        args = [encodeArgument(opt) for opt in args]
        args.append(encodeFilename(ffpp._ffmpeg_filename_argument(tmpfilename), True))

        self._debug_cmd(args)

        # From [1], a PIPE opened in Popen() should be closed, unless
        # .communicate() is called. Avoid leaking any PIPEs by using Popen
        # as a context manager (newer Python 3.x and compat)
        # Fixes "Resource Warning" in test/test_downloader_external.py
        # [1] https://devpress.csdn.net/python/62fde12d7e66823466192e48.html
        with compat_subprocess_Popen(args, stdin=subprocess.PIPE, env=env) as proc:
            try:
                retval = proc.wait()
            except BaseException as e:
                # subprocess.run would send the SIGKILL signal to ffmpeg and the
                # mp4 file couldn't be played, but if we ask ffmpeg to quit it
                # produces a file that is playable (this is mostly useful for live
                # streams). Note that Windows is not affected and produces playable
                # files (see https://github.com/ytdl-org/youtube-dl/issues/8300).
                if isinstance(e, KeyboardInterrupt) and sys.platform != 'win32':
                    process_communicate_or_kill(proc, b'q')
                else:
                    proc.kill()
                raise
        return retval