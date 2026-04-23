def _reader(read_fd: int, stream_name: str, echo_fd: int) -> None:
        buf = bytearray()
        while True:
            try:
                chunk = os.read(read_fd, 4096)
            except OSError as exc:
                if exc.errno == errno.EBADF:
                    break
                continue
            if not chunk:
                break
            # Echo to the original fd so the server console still sees
            # the full output.
            try:
                os.write(echo_fd, chunk)
            except OSError:
                pass
            buf.extend(chunk)
            # Split on \n OR \r so tqdm-style progress bars update.
            while True:
                nl = -1
                for i, b in enumerate(buf):
                    if b == 0x0A or b == 0x0D:
                        nl = i
                        break
                if nl < 0:
                    break
                line = bytes(buf[:nl]).decode("utf-8", errors = "replace")
                del buf[: nl + 1]
                if not line:
                    continue
                if not _log_forward_gate.is_set():
                    # Gate closed (bootstrap phase) -- already echoed to
                    # the saved console fd above; drop the line so the
                    # export dialog doesn't see import / vendoring noise.
                    continue
                try:
                    resp_queue.put_nowait(
                        {
                            "type": "log",
                            "stream": stream_name,
                            "line": line,
                            "ts": time.time(),
                        }
                    )
                except Exception:
                    # Queue put failed (full, closed, etc.) - drop the
                    # line rather than crash the reader thread.
                    pass
        if buf and _log_forward_gate.is_set():
            try:
                resp_queue.put_nowait(
                    {
                        "type": "log",
                        "stream": stream_name,
                        "line": bytes(buf).decode("utf-8", errors = "replace"),
                        "ts": time.time(),
                    }
                )
            except Exception:
                pass