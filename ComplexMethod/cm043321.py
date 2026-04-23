async def create_profile(
        self,
        profile_name: Optional[str] = None,
        browser_config: Optional[BrowserConfig] = None,
        shrink_level: ShrinkLevel = ShrinkLevel.NONE,
    ) -> Optional[str]:
        """
        Creates a browser profile by launching a browser for interactive user setup
        and waits until the user closes it. The profile is stored in a directory that
        can be used later with BrowserConfig.user_data_dir.

        Args:
            profile_name (str, optional): Name for the profile directory.
                If None, a name is generated based on timestamp.
            browser_config (BrowserConfig, optional): Configuration for the browser.
                If None, a default configuration is used with headless=False.
            shrink_level (ShrinkLevel, optional): Optionally shrink profile after creation.
                Default is NONE (no shrinking).

        Returns:
            str: Path to the created profile directory, or None if creation failed

        Example:
            ```python
            profiler = BrowserProfiler()

            # Create a profile interactively
            profile_path = await profiler.create_profile(
                profile_name="my-login-profile"
            )

            # Use the profile in a crawler
            browser_config = BrowserConfig(
                headless=True,
                use_managed_browser=True,
                user_data_dir=profile_path
            )

            async with AsyncWebCrawler(config=browser_config) as crawler:
                # The crawler will now use your profile with all your cookies and login state
                result = await crawler.arun("https://example.com/dashboard")
            ```
        """
        # Create default browser config if none provided
        # IMPORTANT: We disable cookie encryption so profiles can be transferred
        # between machines (e.g., local -> cloud). Without this, Chrome encrypts
        # cookies with OS keychain which isn't portable.
        portable_profile_args = [
            "--password-store=basic",      # Linux: use basic store, not gnome-keyring
            "--use-mock-keychain",         # macOS: use mock keychain, not real one
        ]

        if browser_config is None:
            from .async_configs import BrowserConfig
            browser_config = BrowserConfig(
                browser_type="chromium",
                headless=False,  # Must be visible for user interaction
                verbose=True,
                extra_args=portable_profile_args,
            )
        else:
            # Ensure headless is False for user interaction
            browser_config.headless = False
            # Add portable profile args
            if browser_config.extra_args:
                browser_config.extra_args.extend(portable_profile_args)
            else:
                browser_config.extra_args = portable_profile_args

        # Generate profile name if not provided
        if not profile_name:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            profile_name = f"profile_{timestamp}_{uuid.uuid4().hex[:6]}"

        # Sanitize profile name (replace spaces and special chars)
        profile_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in profile_name)

        # Set user data directory
        profile_path = os.path.join(self.profiles_dir, profile_name)
        os.makedirs(profile_path, exist_ok=True)

        # Print instructions for the user with rich formatting
        border = f"{'='*80}"
        self.logger.info("{border}", tag="PROFILE", params={"border": f"\n{border}"}, colors={"border": LogColor.CYAN})
        self.logger.info("Creating browser profile: {profile_name}", tag="PROFILE", params={"profile_name": profile_name}, colors={"profile_name": LogColor.GREEN})
        self.logger.info("Profile directory: {profile_path}", tag="PROFILE", params={"profile_path": profile_path}, colors={"profile_path": LogColor.YELLOW})

        self.logger.info("\nInstructions:", tag="PROFILE")
        self.logger.info("1. A browser window will open for you to set up your profile.", tag="PROFILE")
        self.logger.info("{segment}, configure settings, etc. as needed.", tag="PROFILE", params={"segment": "2. Log in to websites"}, colors={"segment": LogColor.CYAN})
        self.logger.info("3. When you're done, {segment} to close the browser.", tag="PROFILE", params={"segment": "press 'q' in this terminal"}, colors={"segment": LogColor.YELLOW})
        self.logger.info("4. The profile will be saved and ready to use with Crawl4AI.", tag="PROFILE")
        self.logger.info("{border}", tag="PROFILE", params={"border": f"{border}\n"}, colors={"border": LogColor.CYAN})

        browser_config.headless = False
        browser_config.user_data_dir = profile_path


        # Create managed browser instance
        managed_browser = ManagedBrowser(
            browser_config=browser_config,
            # user_data_dir=profile_path,
            # headless=False,  # Must be visible
            logger=self.logger,
            # debugging_port=browser_config.debugging_port
        )

        # Set up signal handlers to ensure cleanup on interrupt
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)

        # Define cleanup handler for signals
        async def cleanup_handler(sig, frame):
            self.logger.warning("\nCleaning up browser process...", tag="PROFILE")
            await managed_browser.cleanup()
            # Restore original signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
            if sig == signal.SIGINT:
                self.logger.error("Profile creation interrupted. Profile may be incomplete.", tag="PROFILE")
                sys.exit(1)

        # Set signal handlers
        def sigint_handler(sig, frame):
            asyncio.create_task(cleanup_handler(sig, frame))

        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigint_handler)

        # Event to signal when user is done with the browser
        user_done_event = asyncio.Event()

        # Run keyboard input loop in a separate task
        async def listen_for_quit_command():
            """Cross-platform keyboard listener that waits for 'q' key press."""
            # First output the prompt
            self.logger.info(
                "Press {segment} when you've finished using the browser...",
                tag="PROFILE",
                params={"segment": "'q'"}, colors={"segment": LogColor.YELLOW},
                base_color=LogColor.CYAN
            )

            async def check_browser_process():
                """Check if browser process is still running."""
                if (
                    managed_browser.browser_process
                    and managed_browser.browser_process.poll() is not None
                ):
                    self.logger.info(
                        "Browser already closed. Ending input listener.", tag="PROFILE"
                    )
                    user_done_event.set()
                    return True
                return False

            # Try platform-specific implementations with fallback
            try:
                if self._is_windows():
                    await self._listen_windows(user_done_event, check_browser_process, "PROFILE")
                else:
                    await self._listen_unix(user_done_event, check_browser_process, "PROFILE")
            except Exception as e:
                self.logger.warning(f"Platform-specific keyboard listener failed: {e}", tag="PROFILE")
                self.logger.info("Falling back to simple input mode...", tag="PROFILE")
                await self._listen_fallback(user_done_event, check_browser_process, "PROFILE")

        try:
            from playwright.async_api import async_playwright

            # Start the browser
            # await managed_browser.start()
            # 1. ── Start the browser ─────────────────────────────────────────
            cdp_url = await managed_browser.start()

            # 2. ── Attach Playwright to that running Chrome ──────────────────
            pw       = await async_playwright().start()
            browser  = await pw.chromium.connect_over_cdp(cdp_url)
            # Grab the existing default context (there is always one)
            context  = browser.contexts[0]

            # Check if browser started successfully
            browser_process = managed_browser.browser_process
            if not browser_process:
                self.logger.error("Failed to start browser process.", tag="PROFILE")
                return None

            self.logger.info("Browser launched. Waiting for you to finish...", tag="PROFILE") 

            # Start listening for keyboard input
            listener_task = asyncio.create_task(listen_for_quit_command())

            # Wait for either the user to press 'q' or for the browser process to exit naturally
            while not user_done_event.is_set() and browser_process.poll() is None:
                await asyncio.sleep(0.5)

            # Cancel the listener task if it's still running
            if not listener_task.done():
                listener_task.cancel()
                try:
                    await listener_task
                except asyncio.CancelledError:
                    pass

            # 3. ── Persist storage state *before* we kill Chrome ─────────────
            state_file = os.path.join(profile_path, "storage_state.json")
            try:
                await context.storage_state(path=state_file)
                self.logger.info(f"[PROFILE].i  storage_state saved → {state_file}", tag="PROFILE")
            except Exception as e:
                self.logger.warning(f"[PROFILE].w  failed to save storage_state: {e}", tag="PROFILE")

            # 4. ── Close everything cleanly ──────────────────────────────────
            await browser.close()
            await pw.stop()

            # If the browser is still running and the user pressed 'q', terminate it
            if browser_process.poll() is None and user_done_event.is_set():
                self.logger.info("Terminating browser process...", tag="PROFILE")
                await managed_browser.cleanup()

            self.logger.success(f"Browser closed. Profile saved at: {profile_path}", tag="PROFILE")

        except Exception as e:
            self.logger.error(f"Error creating profile: {e!s}", tag="PROFILE")
            await managed_browser.cleanup()
            return None
        finally:
            # Restore original signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)

            # Make sure browser is fully cleaned up
            await managed_browser.cleanup()

        # Shrink profile if requested
        if shrink_level != ShrinkLevel.NONE and profile_path:
            self.logger.info(f"Shrinking profile with level: {shrink_level.value}", tag="PROFILE")
            self.shrink(profile_path, shrink_level)

        return profile_path