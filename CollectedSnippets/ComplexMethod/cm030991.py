def _kill(self) -> None:
        popen = self._popen
        if popen is None:
            return

        if self._killed:
            return
        self._killed = True

        use_killpg = USE_PROCESS_GROUP
        if use_killpg:
            parent_sid = os.getsid(0)
            sid = os.getsid(popen.pid)
            use_killpg = (sid != parent_sid)

        if use_killpg:
            what = f"{self} process group"
        else:
            what = f"{self} process"

        print(f"Kill {what}", file=sys.stderr, flush=True)
        try:
            if use_killpg:
                os.killpg(popen.pid, signal.SIGKILL)
            else:
                popen.kill()
        except ProcessLookupError:
            # popen.kill(): the process completed, the WorkerThread thread
            # read its exit status, but Popen.send_signal() read the returncode
            # just before Popen.wait() set returncode.
            pass
        except OSError as exc:
            print_warning(f"Failed to kill {what}: {exc!r}")