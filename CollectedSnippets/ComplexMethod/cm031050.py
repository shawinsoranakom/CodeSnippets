def _run_repl(
        self,
        repl_input: str | list[str],
        *,
        env: dict | None,
        cmdline_args: list[str] | None,
        cwd: str,
        skip: bool,
        timeout: float,
        exit_on_output: str | None,
    ) -> tuple[str, int]:
        assert pty
        master_fd, slave_fd = pty.openpty()
        cmd = [sys.executable, "-i", "-u"]
        if env is None:
            cmd.append("-I")
        elif "PYTHON_HISTORY" not in env:
            env["PYTHON_HISTORY"] = os.path.join(cwd, ".regrtest_history")
        if cmdline_args is not None:
            cmd.extend(cmdline_args)

        try:
            import termios
        except ModuleNotFoundError:
            pass
        else:
            term_attr = termios.tcgetattr(slave_fd)
            term_attr[6][termios.VREPRINT] = 0  # pass through CTRL-R
            term_attr[6][termios.VINTR] = 0  # pass through CTRL-C
            termios.tcsetattr(slave_fd, termios.TCSANOW, term_attr)

        process = subprocess.Popen(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            cwd=cwd,
            text=True,
            close_fds=True,
            env=env if env else os.environ,
        )
        os.close(slave_fd)
        if isinstance(repl_input, list):
            repl_input = "\n".join(repl_input) + "\n"
        os.write(master_fd, repl_input.encode("utf-8"))

        output = []
        while select.select([master_fd], [], [], timeout)[0]:
            try:
                data = os.read(master_fd, 1024).decode("utf-8")
                if not data:
                    break
            except OSError:
                break
            output.append(data)
            if exit_on_output is not None:
                output = ["".join(output)]
                if exit_on_output in output[0]:
                    process.kill()
                    break
        else:
            os.close(master_fd)
            process.kill()
            process.wait(timeout=timeout)
            self.fail(f"Timeout while waiting for output, got: {''.join(output)}")

        os.close(master_fd)
        try:
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            exit_code = process.wait()
        output = "".join(output)
        if skip and "can't use pyrepl" in output:
            self.skipTest("pyrepl not available")
        return output, exit_code