def _kill_orphaned_servers():
        """Kill orphaned llama-server processes started by studio.

        Only kills processes whose resolved binary lives under a known
        Studio install directory (or matches an exact env-var override)
        to avoid terminating unrelated llama-server instances.

        Mirrors every location that _find_llama_server_binary() can
        return from so that orphans from any supported install path
        are still cleaned up.

        Uses psutil for cross-platform support (Linux, macOS, Windows).
        Falls back to pgrep + /proc/<pid>/exe on Linux when psutil is
        not installed.
        """
        import os
        import signal
        import sys

        try:
            # -- Build the ownership allowlist --------------------------------
            # Two kinds of matches:
            #   exact_binaries  -- env var overrides (exact path match only)
            #   install_roots   -- directory trees that are Studio-owned
            #                      (binary must be *under* one of these)
            install_roots: list[Path] = []

            # Primary install dir (setup.sh / prebuilt installer)
            install_roots.append(Path.home() / ".unsloth" / "llama.cpp")

            # Legacy in-tree build dirs (older setup.sh versions)
            project_root = Path(__file__).resolve().parents[4]
            install_roots.append(project_root / "llama.cpp")

            # Legacy: extracted binary
            install_roots.append(project_root / "bin")

            # UNSLOTH_LLAMA_CPP_PATH env var (custom install dir)
            custom_dir = os.environ.get("UNSLOTH_LLAMA_CPP_PATH")
            if custom_dir:
                install_roots.append(Path(custom_dir))

            # LLAMA_SERVER_PATH env var (exact binary path)
            exact_binaries: list[Path] = []
            env_binary = os.environ.get("LLAMA_SERVER_PATH")
            if env_binary:
                try:
                    exact_binaries.append(Path(env_binary).resolve())
                except OSError:
                    pass

            # Resolve all roots so is_relative_to works reliably
            resolved_roots: list[Path] = []
            for root in install_roots:
                try:
                    resolved_roots.append(root.resolve())
                except OSError:
                    pass

            my_pid = os.getpid()

            # -- Enumerate processes -------------------------------------------
            # Prefer psutil (cross-platform).  Fall back to pgrep + /proc on
            # Linux when psutil is not installed.
            try:
                import psutil

                has_psutil = True
            except ImportError:
                has_psutil = False

            if has_psutil:
                for proc in psutil.process_iter(["pid", "name", "exe"]):
                    try:
                        if proc.info["pid"] == my_pid:
                            continue

                        name = proc.info.get("name") or ""
                        if not name.lower().startswith("llama-server"):
                            continue

                        exe = proc.info.get("exe")
                        if not exe:
                            continue

                        exe_path = Path(exe).resolve()

                        # Check ownership: exact binary match OR binary is
                        # under a known install root (proper ancestry, not
                        # substring).
                        is_ours = exe_path in exact_binaries or any(
                            exe_path.is_relative_to(root) for root in resolved_roots
                        )
                        if not is_ours:
                            continue

                        proc.kill()
                        logger.info(
                            f"Killed orphaned llama-server process "
                            f"(pid={proc.info['pid']})"
                        )
                    except (
                        psutil.NoSuchProcess,
                        psutil.AccessDenied,
                        psutil.ZombieProcess,
                    ):
                        pass
            else:
                # -- Fallback: pgrep + /proc/<pid>/exe (Linux only) -----------
                if sys.platform != "linux":
                    return
                result = subprocess.run(
                    ["pgrep", "-a", "-f", "llama-server"],
                    capture_output = True,
                    text = True,
                    timeout = 5,
                )
                if result.returncode != 0:
                    return

                for line in result.stdout.strip().splitlines():
                    parts = line.strip().split(None, 1)
                    if len(parts) < 2:
                        continue
                    pid = int(parts[0])
                    if pid == my_pid:
                        continue

                    # Resolve the actual executable.  /proc/<pid>/exe is a
                    # symlink to the real binary and avoids all cmdline-
                    # parsing ambiguities (spaces in paths, argv rewriting).
                    # Fall back to the first cmdline token when /proc is
                    # unavailable.
                    proc_exe = Path(f"/proc/{pid}/exe")
                    try:
                        binary = proc_exe.resolve(strict = True)
                    except (OSError, ValueError):
                        cmdline = parts[1]
                        token = cmdline.split()[0] if cmdline.strip() else ""
                        if not token:
                            continue
                        binary = Path(token).resolve(strict = False)

                    owned = binary in exact_binaries or any(
                        binary.is_relative_to(root) for root in resolved_roots
                    )
                    if not owned:
                        continue

                    try:
                        os.kill(pid, signal.SIGKILL)
                        logger.info(f"Killed orphaned llama-server process (pid={pid})")
                    except ProcessLookupError:
                        pass
                    except PermissionError:
                        pass
        except Exception:
            logger.warning("Error during orphan server cleanup", exc_info = True)