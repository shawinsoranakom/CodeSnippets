def __call__(self) -> int:
        """ Install a package using the Subprocess module

        Returns
        -------
        int
            The return code of the package install process
        """
        with Popen(self._command,
                   bufsize=0, stdout=PIPE, stderr=PIPE) as proc:
            lines = b""
            while True:
                if proc.stdout is not None:
                    lines = proc.stdout.readline()
                returncode = proc.poll()
                if lines == b"" and returncode is not None:
                    break
                for line in lines.split(b"\r"):
                    clean = self._seen_line_log(line.decode("utf-8", errors="replace"))
                    if not self._is_gui and clean:
                        self._status(clean)
            if returncode and proc.stderr is not None:
                for line in proc.stderr.readlines():
                    clean = self._seen_line_log(line.decode("utf-8", errors="replace"),
                                                is_error=True)
                    if clean:
                        self.error_lines.append(clean.replace("ERROR:", "").strip())

        logger.debug("Packages: %s, returncode: %s", self._packages, returncode)
        if not self._is_gui:
            self._status.close()
        return returncode