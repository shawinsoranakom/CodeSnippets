async def _lazy_init(
        self,
    ) -> None:
        """
        On the first call, we initialize the browser and the page.
        """

        # Check the current event loop policy if on windows.
        if sys.platform == "win32":
            current_policy = asyncio.get_event_loop_policy()
            if hasattr(asyncio, "WindowsProactorEventLoopPolicy") and not isinstance(
                current_policy, asyncio.WindowsProactorEventLoopPolicy
            ):
                warnings.warn(
                    "The current event loop policy is not WindowsProactorEventLoopPolicy. "
                    "This may cause issues with subprocesses. "
                    "Try setting the event loop policy to WindowsProactorEventLoopPolicy. "
                    "For example: `asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())`. "
                    "See https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.ProactorEventLoop.",
                    stacklevel=2,
                )

        self._last_download = None
        self._prior_metadata_hash = None

        # Create the playwright self
        launch_args: Dict[str, Any] = {"headless": self.headless}
        if self.browser_channel is not None:
            launch_args["channel"] = self.browser_channel
        if self._playwright is None:
            self._playwright = await async_playwright().start()

        # Create the context -- are we launching persistent?
        if self._context is None:
            if self.browser_data_dir is None:
                browser = await self._playwright.chromium.launch(**launch_args)
                self._context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
                )
            else:
                self._context = await self._playwright.chromium.launch_persistent_context(
                    self.browser_data_dir, **launch_args
                )

        # Create the page
        self._context.set_default_timeout(60000)  # One minute
        self._page = await self._context.new_page()
        assert self._page is not None
        # self._page.route(lambda x: True, self._route_handler)
        self._page.on("download", self._download_handler)
        if self.to_resize_viewport:
            await self._page.set_viewport_size({"width": self.VIEWPORT_WIDTH, "height": self.VIEWPORT_HEIGHT})
        await self._page.add_init_script(
            path=os.path.join(os.path.abspath(os.path.dirname(__file__)), "page_script.js")
        )
        await self._page.goto(self.start_page)
        await self._page.wait_for_load_state()

        # Prepare the debug directory -- which stores the screenshots generated throughout the process
        await self._set_debug_dir(self.debug_dir)
        self.did_lazy_init = True