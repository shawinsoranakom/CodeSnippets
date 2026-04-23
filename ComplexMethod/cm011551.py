def redirect(std: str, to_file: str):
        """
        Redirect ``std`` (one of ``"stdout"`` or ``"stderr"``) to a file at ``to_file``.

        On Windows this performs a four-layer redirect:

        1. ``sys.stdout``/``sys.stderr`` -- rewired to a new TextIOWrapper so
           Python's ``print()`` writes to the destination file.
        2. CRT fd (``_dup2``) -- captures C ``printf`` and UCRT ``FILE*`` writers.
        3. Win32 ``SetStdHandle`` -- captures native code using ``WriteFile``/
           ``WriteConsole`` directly, including HIP/ROCm.
        4. ``fflush`` before each switch -- prevents lost output from CRT buffering.

        .. note:: If ROCm/HIP caches the Win32 HANDLE before this redirect runs
                  (e.g. at ``import torch`` time), set up the redirect *before*
                  importing torch/ROCm to capture all output.

        Directory of ``to_file`` is assumed to exist. The destination file is
        overwritten if it already exists.
        """
        if std not in _VALID_STD:
            raise ValueError(
                f"unknown standard stream <{std}>, must be one of {_VALID_STD}"
            )

        std_fd = 1 if std == "stdout" else 2
        win32_handle_id = _WIN32_STD_HANDLE[std]
        orig_sys_std = getattr(sys, std)
        orig_fd_dup = _crt_dup(std_fd)
        if orig_fd_dup == -1:
            raise OSError(f"CRT _dup failed for {std} (fd={std_fd})")
        orig_win32_handle = _kernel32.GetStdHandle(win32_handle_id)

        with open(to_file, mode="w+b") as dst:
            dst_fd = dst.fileno()

            try:
                libc.fflush(_c_std(std))
            except Exception:
                pass
            try:
                orig_sys_std.flush()
            except Exception:
                pass

            _kernel32.SetStdHandle(
                win32_handle_id,
                _msvcrt.get_osfhandle(dst_fd),  # pyrefly: ignore [missing-attribute]
            )

            if _crt_dup2(dst_fd, std_fd) == -1:
                raise OSError(f"CRT _dup2 failed redirecting {std}")

            new_sys_std = _io.TextIOWrapper(
                open(dst_fd, mode="wb", closefd=False),  # noqa: SIM115
                encoding=orig_sys_std.encoding or "utf-8",
                errors="replace",
                line_buffering=True,
            )
            setattr(sys, std, new_sys_std)

            try:
                yield
            finally:
                try:
                    new_sys_std.flush()
                except Exception:
                    pass
                try:
                    libc.fflush(_c_std(std))
                except Exception:
                    pass

                setattr(sys, std, orig_sys_std)
                _crt_dup2(orig_fd_dup, std_fd)
                os.close(orig_fd_dup)
                _kernel32.SetStdHandle(win32_handle_id, orig_win32_handle)