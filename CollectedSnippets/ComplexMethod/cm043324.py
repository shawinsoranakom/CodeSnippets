async def launch_standalone_browser(self, 
                                  browser_type: str = "chromium",
                                  user_data_dir: Optional[str] = None,
                                  debugging_port: int = 9222,
                                  headless: bool = False,
                                  save_as_builtin: bool = False) -> Optional[str]:
        """
        Launch a standalone browser with CDP debugging enabled and keep it running
        until the user presses 'q'. Returns and displays the CDP URL.

        Args:
            browser_type (str): Type of browser to launch ('chromium' or 'firefox')
            user_data_dir (str, optional): Path to user profile directory
            debugging_port (int): Port to use for CDP debugging
            headless (bool): Whether to run in headless mode

        Returns:
            str: CDP URL for the browser, or None if launch failed

        Example:
            ```python
            profiler = BrowserProfiler()
            cdp_url = await profiler.launch_standalone_browser(
                user_data_dir="/path/to/profile",
                debugging_port=9222
            )
            # Use cdp_url to connect to the browser
            ```
        """
        # Use the provided directory if specified, otherwise create a temporary directory
        if user_data_dir:
            # Directory is provided directly, ensure it exists
            profile_path = user_data_dir
            os.makedirs(profile_path, exist_ok=True)
        else:
            # Create a temporary profile directory
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            profile_name = f"temp_{timestamp}_{uuid.uuid4().hex[:6]}"
            profile_path = os.path.join(self.profiles_dir, profile_name)
            os.makedirs(profile_path, exist_ok=True)

        # Print initial information
        border = f"{'='*80}"
        self.logger.info("{border}", tag="CDP", params={"border": border}, colors={"border": LogColor.CYAN})
        self.logger.info("Launching standalone browser with CDP debugging", tag="CDP")
        self.logger.info("Browser type: {browser_type}", tag="CDP", params={"browser_type": browser_type}, colors={"browser_type": LogColor.CYAN})
        self.logger.info("Profile path: {profile_path}", tag="CDP", params={"profile_path": profile_path}, colors={"profile_path": LogColor.YELLOW})
        self.logger.info(f"Debugging port: {debugging_port}", tag="CDP")
        self.logger.info(f"Headless mode: {headless}", tag="CDP")

        # create browser config
        browser_config = BrowserConfig(
            browser_type=browser_type,
            headless=headless,
            user_data_dir=profile_path,
            debugging_port=debugging_port,
            verbose=True
        )

        # Create managed browser instance
        managed_browser = ManagedBrowser(
            browser_config=browser_config,
            user_data_dir=profile_path,
            headless=headless,
            logger=self.logger,
            debugging_port=debugging_port
        )

        # Set up signal handlers to ensure cleanup on interrupt
        original_sigint = signal.getsignal(signal.SIGINT)
        original_sigterm = signal.getsignal(signal.SIGTERM)

        # Define cleanup handler for signals
        async def cleanup_handler(sig, frame):
            self.logger.warning("\nCleaning up browser process...", tag="CDP")
            await managed_browser.cleanup()
            # Restore original signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)
            if sig == signal.SIGINT:
                self.logger.error("Browser terminated by user.", tag="CDP")
                sys.exit(1)

        # Set signal handlers
        def sigint_handler(sig, frame):
            asyncio.create_task(cleanup_handler(sig, frame))

        signal.signal(signal.SIGINT, sigint_handler)
        signal.signal(signal.SIGTERM, sigint_handler)

        # Event to signal when user wants to exit
        user_done_event = asyncio.Event()

        # Run keyboard input loop in a separate task
        async def listen_for_quit_command():
            """Cross-platform keyboard listener that waits for 'q' key press."""
            # First output the prompt
            self.logger.info(
                "Press {segment} to stop the browser and exit...",
                tag="CDP",
                params={"segment": "'q'"}, colors={"segment": LogColor.YELLOW},
                base_color=LogColor.CYAN
            )

            async def check_browser_process():
                """Check if browser process is still running."""
                if managed_browser.browser_process and managed_browser.browser_process.poll() is not None:
                    self.logger.info("Browser already closed. Ending input listener.", tag="CDP")
                    user_done_event.set()
                    return True
                return False

            # Try platform-specific implementations with fallback
            try:
                if self._is_windows():
                    await self._listen_windows(user_done_event, check_browser_process, "CDP")
                else:
                    await self._listen_unix(user_done_event, check_browser_process, "CDP")
            except Exception as e:
                self.logger.warning(f"Platform-specific keyboard listener failed: {e}", tag="CDP")
                self.logger.info("Falling back to simple input mode...", tag="CDP")
                await self._listen_fallback(user_done_event, check_browser_process, "CDP")

        # Function to retrieve and display CDP JSON config
        async def get_cdp_json(port):
            import aiohttp
            cdp_url = f"http://localhost:{port}"
            json_url = f"{cdp_url}/json/version"

            try:
                async with aiohttp.ClientSession() as session:
                    # Try multiple times in case the browser is still starting up
                    for _ in range(10):
                        try:
                            async with session.get(json_url) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    return cdp_url, data
                        except Exception:
                            pass

                        await asyncio.sleep(0.5)

                    return cdp_url, None
            except Exception as e:
                self.logger.error(f"Error fetching CDP JSON: {str(e)}", tag="CDP")
                return cdp_url, None

        cdp_url = None
        config_json = None

        try:
            # Start the browser
            await managed_browser.start()

            # Check if browser started successfully
            browser_process = managed_browser.browser_process
            if not browser_process:
                self.logger.error("Failed to start browser process.", tag="CDP")
                return None

            self.logger.info("Browser launched successfully. Retrieving CDP information...", tag="CDP") 

            # Get CDP URL and JSON config
            cdp_url, config_json = await get_cdp_json(debugging_port)

            if cdp_url:
                self.logger.success(f"CDP URL: {cdp_url}", tag="CDP")

                if config_json:
                    # Display relevant CDP information
                    self.logger.info(f"Browser: {config_json.get('Browser', 'Unknown')}", tag="CDP", colors={"Browser": LogColor.CYAN})
                    self.logger.info(f"Protocol Version: {config_json.get('Protocol-Version', 'Unknown')}", tag="CDP", colors={"Protocol-Version": LogColor.CYAN})
                    if 'webSocketDebuggerUrl' in config_json:
                        self.logger.info("WebSocket URL: {webSocketDebuggerUrl}", tag="CDP", params={"webSocketDebuggerUrl": config_json['webSocketDebuggerUrl']}, colors={"webSocketDebuggerUrl": LogColor.GREEN})
                else:
                    self.logger.warning("Could not retrieve CDP configuration JSON", tag="CDP")
            else:
                self.logger.error(f"Failed to get CDP URL on port {debugging_port}", tag="CDP")
                await managed_browser.cleanup()
                return None

            # Start listening for keyboard input
            listener_task = asyncio.create_task(listen_for_quit_command())

            # Wait for the user to press 'q' or for the browser process to exit naturally
            while not user_done_event.is_set() and browser_process.poll() is None:
                await asyncio.sleep(0.5)

            # Cancel the listener task if it's still running
            if not listener_task.done():
                listener_task.cancel()
                try:
                    await listener_task
                except asyncio.CancelledError:
                    pass

            # If the browser is still running and the user pressed 'q', terminate it
            if browser_process.poll() is None and user_done_event.is_set():
                self.logger.info("Terminating browser process...", tag="CDP")
                await managed_browser.cleanup()

            self.logger.success("Browser closed.", tag="CDP")

        except Exception as e:
            self.logger.error(f"Error launching standalone browser: {str(e)}", tag="CDP")
            await managed_browser.cleanup()
            return None
        finally:
            # Restore original signal handlers
            signal.signal(signal.SIGINT, original_sigint)
            signal.signal(signal.SIGTERM, original_sigterm)

            # Make sure browser is fully cleaned up
            await managed_browser.cleanup()

        # Return the CDP URL
        return cdp_url