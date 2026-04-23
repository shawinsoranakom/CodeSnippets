def _kill_process_group_survivors(
        self, pgid: int | None, timeout: float = 15.0
    ) -> None:
        """SIGKILL any processes still in the server's process group
        and wait for them to exit.

        Because the server is launched with ``start_new_session=True``,
        all its children (EngineCore, workers, etc.) share the same
        pgid. After the root process is killed, stragglers -- especially
        on ROCm where GPU contexts linger until the *process* exits --
        must be reaped explicitly.

        Uses ``/proc`` to scan for pgid members so this works even after
        the parent has been reaped (unlike ``psutil.Process.children``).
        """
        if pgid is None:
            return

        # Send SIGKILL to the entire process group one more time.
        # This is cheap and harmless if everyone is already dead.
        with contextlib.suppress(ProcessLookupError, OSError):
            os.killpg(pgid, signal.SIGKILL)

        # Collect surviving PIDs by scanning /proc for matching pgid.
        # This works on Linux even after the parent has been waited on
        # and is more reliable than psutil.Process(parent).children().
        survivor_pids = self._find_pgid_members(pgid)

        if not survivor_pids:
            return

        print(
            f"[RemoteOpenAIServer] {len(survivor_pids)} process(es) still "
            f"in pgid {pgid} after SIGKILL: {survivor_pids}"
        )

        # Wait for each survivor to actually exit so the GPU driver
        # releases its VRAM.
        deadline = time.time() + timeout
        while survivor_pids and time.time() < deadline:
            still_alive = []
            for spid in survivor_pids:
                try:
                    os.kill(spid, 0)  # Check if still alive
                    still_alive.append(spid)
                except (ProcessLookupError, OSError):
                    pass
            survivor_pids = still_alive
            if survivor_pids:
                time.sleep(0.5)

        if survivor_pids:
            print(
                f"[RemoteOpenAIServer] WARNING: processes {survivor_pids} "
                f"in pgid {pgid} could not be killed within {timeout}s"
            )