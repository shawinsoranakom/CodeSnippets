async def launch_builtin_browser(self, 
                                 browser_type: str = "chromium",
                                 debugging_port: int = 9222,
                                 headless: bool = True) -> Optional[str]:
        """
        Launch a browser in the background for use as the builtin browser.

        Args:
            browser_type (str): Type of browser to launch ('chromium' or 'firefox')
            debugging_port (int): Port to use for CDP debugging
            headless (bool): Whether to run in headless mode

        Returns:
            str: CDP URL for the browser, or None if launch failed
        """
        # Check if there's an existing browser still running
        browser_info = self.get_builtin_browser_info()
        if browser_info and self._is_browser_running(browser_info.get('pid')):
            self.logger.info("Builtin browser is already running", tag="BUILTIN")
            return browser_info.get('cdp_url')

        # Create a user data directory for the builtin browser
        user_data_dir = os.path.join(self.builtin_browser_dir, "user_data")
        os.makedirs(user_data_dir, exist_ok=True)

        # Create managed browser instance
        managed_browser = ManagedBrowser(
            browser_type=browser_type,
            user_data_dir=user_data_dir,
            headless=headless,
            logger=self.logger,
            debugging_port=debugging_port
        )

        try:
            # Start the browser
            await managed_browser.start()

            # Check if browser started successfully
            browser_process = managed_browser.browser_process
            if not browser_process:
                self.logger.error("Failed to start browser process.", tag="BUILTIN")
                return None

            # Get CDP URL
            cdp_url = f"http://localhost:{debugging_port}"

            # Try to verify browser is responsive by fetching version info
            import aiohttp
            json_url = f"{cdp_url}/json/version"
            config_json = None

            try:
                async with aiohttp.ClientSession() as session:
                    for _ in range(10):  # Try multiple times
                        try:
                            async with session.get(json_url) as response:
                                if response.status == 200:
                                    config_json = await response.json()
                                    break
                        except Exception:
                            pass
                        await asyncio.sleep(0.5)
            except Exception as e:
                self.logger.warning(f"Could not verify browser: {str(e)}", tag="BUILTIN")

            # Save browser info
            browser_info = {
                'pid': browser_process.pid,
                'cdp_url': cdp_url,
                'user_data_dir': user_data_dir,
                'browser_type': browser_type,
                'debugging_port': debugging_port,
                'start_time': time.time(),
                'config': config_json
            }

            with open(self.builtin_config_file, 'w') as f:
                json.dump(browser_info, f, indent=2)

            # Detach from the browser process - don't keep any references
            # This is important to allow the Python script to exit while the browser continues running
            # We'll just record the PID and other info, and the browser will run independently
            managed_browser.browser_process = None

            self.logger.success(f"Builtin browser launched at CDP URL: {cdp_url}", tag="BUILTIN")
            return cdp_url

        except Exception as e:
            self.logger.error(f"Error launching builtin browser: {str(e)}", tag="BUILTIN")
            if managed_browser:
                await managed_browser.cleanup()
            return None