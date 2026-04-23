def real_run_ffmpeg(self, input_path_opts, output_path_opts, *, expected_retcodes=(0,)):
        self.check_version()

        oldest_mtime = min(
            os.stat(path).st_mtime for path, _ in input_path_opts if path)

        cmd = [self.executable, encodeArgument('-y')]
        # avconv does not have repeat option
        if self.basename == 'ffmpeg':
            cmd += [encodeArgument('-loglevel'), encodeArgument('repeat+info')]

        def make_args(file, args, name, number):
            keys = [f'_{name}{number}', f'_{name}']
            if name == 'o':
                args += ['-movflags', '+faststart']
                if number == 1:
                    keys.append('')
            args += self._configuration_args(self.basename, keys)
            if name == 'i':
                args.append('-i')
            return (
                [encodeArgument(arg) for arg in args]
                + [self._ffmpeg_filename_argument(file)])

        for arg_type, path_opts in (('i', input_path_opts), ('o', output_path_opts)):
            cmd += itertools.chain.from_iterable(
                make_args(path, list(opts), arg_type, i + 1)
                for i, (path, opts) in enumerate(path_opts) if path)

        self.write_debug(f'ffmpeg command line: {shell_quote(cmd)}')
        _, stderr, returncode = Popen.run(
            cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
        if returncode not in variadic(expected_retcodes):
            self.write_debug(stderr)
            raise FFmpegPostProcessorError(stderr.strip().splitlines()[-1])
        for out_path, _ in output_path_opts:
            if out_path:
                self.try_utime(out_path, oldest_mtime, oldest_mtime)
        return stderr