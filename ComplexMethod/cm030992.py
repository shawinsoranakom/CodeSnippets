def _run_process(self, runtests: WorkerRunTests, output_fd: int,
                     tmp_dir: StrPath | None = None) -> int | None:
        popen = create_worker_process(runtests, output_fd, tmp_dir)
        self._popen = popen
        self._killed = False

        try:
            if self._stopped:
                # If kill() has been called before self._popen is set,
                # self._popen is still running. Call again kill()
                # to ensure that the process is killed.
                self._kill()
                raise ExitThread

            try:
                # gh-94026: stdout+stderr are written to tempfile
                retcode = popen.wait(timeout=self.timeout)
                assert retcode is not None
                return retcode
            except subprocess.TimeoutExpired:
                if self._stopped:
                    # kill() has been called: communicate() fails on reading
                    # closed stdout
                    raise ExitThread

                # On timeout, kill the process
                self._kill()

                # None means TIMEOUT for the caller
                retcode = None
                # bpo-38207: Don't attempt to call communicate() again: on it
                # can hang until all child processes using stdout
                # pipes completes.
            except OSError:
                if self._stopped:
                    # kill() has been called: communicate() fails
                    # on reading closed stdout
                    raise ExitThread
                raise
            return None
        except:
            self._kill()
            raise
        finally:
            self._wait_completed()
            self._popen = None