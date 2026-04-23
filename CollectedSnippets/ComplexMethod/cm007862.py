def run_ffmpeg_multiple_files(self, input_paths, out_path, opts):
        self.check_version()

        oldest_mtime = min(
            os.stat(encodeFilename(path)).st_mtime for path in input_paths)

        opts += self._configuration_args()

        files_cmd = []
        for path in input_paths:
            files_cmd.extend([
                encodeArgument('-i'),
                encodeFilename(self._ffmpeg_filename_argument(path), True)
            ])
        cmd = [encodeFilename(self.executable, True), encodeArgument('-y')]
        # avconv does not have repeat option
        if self.basename == 'ffmpeg':
            cmd += [encodeArgument('-loglevel'), encodeArgument('repeat+info')]
        cmd += (files_cmd
                + [encodeArgument(o) for o in opts]
                + [encodeFilename(self._ffmpeg_filename_argument(out_path), True)])

        if self._downloader.params.get('verbose', False):
            self._downloader.to_screen('[debug] ffmpeg command line: %s' % shell_quote(cmd))
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        stdout, stderr = process_communicate_or_kill(p)
        if p.returncode != 0:
            stderr = stderr.decode('utf-8', 'replace')
            msgs = stderr.strip().split('\n')
            msg = msgs[-1]
            if self._downloader.params.get('verbose', False):
                self._downloader.to_screen('[debug] ' + '\n'.join(msgs[:-1]))
            raise FFmpegPostProcessorError(msg)
        self.try_utime(out_path, oldest_mtime, oldest_mtime)