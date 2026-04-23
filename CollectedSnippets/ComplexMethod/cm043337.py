async def start(self) -> str:
        """
        Starts the browser process or returns CDP endpoint URL.
        If cdp_url is provided, returns it directly.
        If user_data_dir is not provided for local browser, creates a temporary directory.

        Returns:
            str: CDP endpoint URL
        """
        # If CDP URL provided, just return it
        if self.cdp_url:
            return self.cdp_url

        # Create temp dir if needed
        if not self.user_data_dir:
            self.temp_dir = tempfile.mkdtemp(prefix="browser-profile-")
            self.user_data_dir = self.temp_dir

        # Get browser path and args based on OS and browser type
        # browser_path = self._get_browser_path()
        args = await self._get_browser_args()

        if self.browser_config.extra_args:
            args.extend(self.browser_config.extra_args)


        # ── make sure no old Chromium instance is owning the same port/profile ──
        try:
            if sys.platform == "win32":
                if psutil is None:
                    raise RuntimeError("psutil not available, cannot clean old browser")
                for p in psutil.process_iter(["pid", "name", "cmdline"]):
                    cl = " ".join(p.info.get("cmdline") or [])
                    if (
                        f"--remote-debugging-port={self.debugging_port}" in cl
                        and f"--user-data-dir={self.user_data_dir}" in cl
                    ):
                        p.kill()
                        p.wait(timeout=5)
            else:  # macOS / Linux
                # kill any process listening on the same debugging port
                try:
                    pids = (
                        subprocess.check_output(
                            shlex.split(f"lsof -t -i:{self.debugging_port}"),
                            stderr=subprocess.DEVNULL,
                        )
                        .decode()
                        .strip()
                        .splitlines()
                    )
                except (FileNotFoundError, subprocess.CalledProcessError):
                    pids = []
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                    except ProcessLookupError:
                        pass

                # remove Chromium singleton locks, or new launch exits with
                # “Opening in existing browser session.”
                for f in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
                    fp = os.path.join(self.user_data_dir, f)
                    if os.path.exists(fp):
                        os.remove(fp)
        except Exception as _e:
            # non-fatal — we'll try to start anyway, but log what happened
            self.logger.warning(f"pre-launch cleanup failed: {_e}", tag="BROWSER")            


        # Start browser process
        try:
            # Use DETACHED_PROCESS flag on Windows to fully detach the process
            # On Unix, we'll use preexec_fn=os.setpgrp to start the process in a new process group
            if sys.platform == "win32":
                self.browser_process = subprocess.Popen(
                    args, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                self.browser_process = subprocess.Popen(
                    args, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE,
                    preexec_fn=os.setpgrp  # Start in a new process group
                )

            # If verbose is True print args used to run the process
            if self.logger and self.browser_config.verbose:
                self.logger.debug(
                    f"Starting browser with args: {' '.join(args)}",
                    tag="BROWSER"
                )    

            # We'll monitor for a short time to make sure it starts properly, but won't keep monitoring
            await asyncio.sleep(0.5)  # Give browser time to start
            await self._initial_startup_check()
            await asyncio.sleep(2)  # Give browser time to start
            return f"http://{self.host}:{self.debugging_port}"
        except Exception as e:
            await self.cleanup()
            raise Exception(f"Failed to start browser: {e}")