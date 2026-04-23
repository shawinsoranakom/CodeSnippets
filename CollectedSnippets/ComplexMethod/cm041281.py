def do_run_cmd(self):
        def convert_line(line):
            line = to_str(line or "")
            if self.strip_color:
                # strip color codes
                line = re.sub(r"\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))", "", line)
            return f"{line.strip()}\r\n"

        def filter_line(line):
            """Return True if this line should be filtered, i.e., not printed"""
            return "(Press CTRL+C to quit)" in line

        outfile = self.outfile or os.devnull
        if self.log_listener and outfile == os.devnull:
            outfile = subprocess.PIPE
        try:
            self.process = run(
                self.cmd,
                asynchronous=True,
                stdin=self.stdin,
                outfile=outfile,
                env_vars=self.env_vars,
                inherit_cwd=self.inherit_cwd,
                inherit_env=self.inherit_env,
                cwd=self.cwd,
            )
            self.started.set()
            if outfile:
                if outfile == subprocess.PIPE:
                    # get stdout/stderr from child process and write to parent output
                    streams = (
                        (self.process.stdout, sys.stdout),
                        (self.process.stderr, sys.stderr),
                    )
                    for instream, outstream in streams:
                        if not instream:
                            continue
                        for line in iter(instream.readline, None):
                            # `line` should contain a newline at the end as we're iterating,
                            # hence we can safely break the loop if `line` is None or empty string
                            if line in [None, "", b""]:
                                break
                            if not (line and line.strip()) and self.is_killed():
                                break
                            line = convert_line(line)
                            if filter_line(line):
                                continue
                            if self.log_listener:
                                self.log_listener(line, stream=instream)
                            if self.outfile not in [None, os.devnull]:
                                outstream.write(line)
                                outstream.flush()
                if self.process:
                    self.process.wait()
            else:
                self.process.communicate()
        except Exception as e:
            self.result_future.set_exception(e)
            if self.process and not self.quiet:
                LOG.warning('Shell command error "%s": %s', e, self.cmd)
        if self.process and not self.quiet and self.process.returncode != 0:
            LOG.warning('Shell command exit code "%s": %s', self.process.returncode, self.cmd)