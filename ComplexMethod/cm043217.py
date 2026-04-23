def __init__(
        self,
        browser_type: str = "chromium",
        headless: bool = True,
        browser_mode: str = "dedicated",
        use_managed_browser: bool = False,
        cdp_url: str = None,
        browser_context_id: str = None,
        target_id: str = None,
        cdp_cleanup_on_close: bool = False,
        cdp_close_delay: float = 1.0,
        cache_cdp_connection: bool = False,
        create_isolated_context: bool = False,
        use_persistent_context: bool = False,
        user_data_dir: str = None,
        chrome_channel: str = "chromium",
        channel: str = "chromium",
        proxy: str = None,
        proxy_config: Union[ProxyConfig, dict, None] = None,
        viewport_width: int = 1080,
        viewport_height: int = 600,
        viewport: dict = None,
        device_scale_factor: float = 1.0,
        accept_downloads: bool = False,
        downloads_path: str = None,
        storage_state: Union[str, dict, None] = None,
        ignore_https_errors: bool = True,
        java_script_enabled: bool = True,
        sleep_on_close: bool = False,
        verbose: bool = True,
        cookies: list = None,
        headers: dict = None,
        user_agent: str = (
            # "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) AppleWebKit/537.36 "
            # "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            # "(KHTML, like Gecko) Chrome/116.0.5845.187 Safari/604.1 Edg/117.0.2045.47"
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0.0.0 Safari/537.36"
        ),
        user_agent_mode: str = "",
        user_agent_generator_config: dict = {},
        text_mode: bool = False,
        light_mode: bool = False,
        extra_args: list = None,
        debugging_port: int = 9222,
        host: str = "localhost",
        enable_stealth: bool = False,
        avoid_ads: bool = False,
        avoid_css: bool = False,
        init_scripts: List[str] = None,
        memory_saving_mode: bool = False,
        max_pages_before_recycle: int = 0,
    ):

        self.browser_type = browser_type
        self.headless = headless
        self.browser_mode = browser_mode
        self.use_managed_browser = use_managed_browser
        self.cdp_url = cdp_url
        self.browser_context_id = browser_context_id
        self.target_id = target_id
        self.cdp_cleanup_on_close = cdp_cleanup_on_close
        self.cdp_close_delay = cdp_close_delay
        self.cache_cdp_connection = cache_cdp_connection
        self.create_isolated_context = create_isolated_context
        self.use_persistent_context = use_persistent_context
        self.user_data_dir = user_data_dir
        self.chrome_channel = chrome_channel or self.browser_type or "chromium"
        self.channel = channel or self.browser_type or "chromium"
        if self.browser_type in ["firefox", "webkit"]:
            self.channel = ""
            self.chrome_channel = ""
        if proxy:
            warnings.warn("The 'proxy' parameter is deprecated and will be removed in a future release. Use 'proxy_config' instead.", UserWarning)
        self.proxy = proxy
        self.proxy_config = proxy_config
        if isinstance(self.proxy_config, dict):
            self.proxy_config = ProxyConfig.from_dict(self.proxy_config)
        if isinstance(self.proxy_config, str):
            self.proxy_config = ProxyConfig.from_string(self.proxy_config)

        if self.proxy and self.proxy_config:
            warnings.warn("Both 'proxy' and 'proxy_config' are provided. 'proxy_config' will take precedence.", UserWarning)
            self.proxy = None
        elif self.proxy:
            # Convert proxy string to ProxyConfig if proxy_config is not provided
            self.proxy_config = ProxyConfig.from_string(self.proxy)
            self.proxy = None

        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.viewport = viewport
        if self.viewport is not None:
            self.viewport_width = self.viewport.get("width", 1080)
            self.viewport_height = self.viewport.get("height", 600)
        self.device_scale_factor = device_scale_factor
        self.accept_downloads = accept_downloads
        self.downloads_path = downloads_path
        self.storage_state = storage_state
        self.ignore_https_errors = ignore_https_errors
        self.java_script_enabled = java_script_enabled
        self.cookies = cookies if cookies is not None else []
        self.headers = headers if headers is not None else {}
        self.user_agent = user_agent
        self.user_agent_mode = user_agent_mode
        self.user_agent_generator_config = user_agent_generator_config
        self.text_mode = text_mode
        self.light_mode = light_mode
        self.extra_args = extra_args if extra_args is not None else []
        self.sleep_on_close = sleep_on_close
        self.verbose = verbose
        self.debugging_port = debugging_port
        self.host = host
        self.enable_stealth = enable_stealth
        self.avoid_ads = avoid_ads
        self.avoid_css = avoid_css
        self.init_scripts = init_scripts if init_scripts is not None else []
        self.memory_saving_mode = memory_saving_mode
        self.max_pages_before_recycle = max_pages_before_recycle

        fa_user_agenr_generator = ValidUAGenerator()
        if self.user_agent_mode == "random":
            self.user_agent = fa_user_agenr_generator.generate(
                **(self.user_agent_generator_config or {})
            )
        else:
            pass

        self.browser_hint = UAGen.generate_client_hints(self.user_agent)
        self.headers.setdefault("sec-ch-ua", self.browser_hint)

        # Set appropriate browser management flags based on browser_mode
        if self.browser_mode == "builtin":
            # Builtin mode uses managed browser connecting to builtin CDP endpoint
            self.use_managed_browser = True
            # cdp_url will be set later by browser_manager
        elif self.browser_mode == "docker":
            # Docker mode uses managed browser with CDP to connect to browser in container
            self.use_managed_browser = True
            # cdp_url will be set later by docker browser strategy
        elif self.browser_mode == "custom" and self.cdp_url:
            # Custom mode with explicit CDP URL
            self.use_managed_browser = True
        elif self.browser_mode == "dedicated":
            # Dedicated mode uses a new browser instance each time
            pass

        # If persistent context is requested, ensure managed browser is enabled
        if self.use_persistent_context:
            self.use_managed_browser = True

        # Validate stealth configuration
        if self.enable_stealth and self.use_managed_browser and self.browser_mode == "builtin":
            raise ValueError(
                "enable_stealth cannot be used with browser_mode='builtin'. "
                "Stealth mode requires a dedicated browser instance."
            )