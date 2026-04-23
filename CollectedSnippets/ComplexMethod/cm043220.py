def __init__(
        self,
        # Content Processing Parameters
        word_count_threshold: int = MIN_WORD_THRESHOLD,
        extraction_strategy: ExtractionStrategy = None,
        chunking_strategy: ChunkingStrategy = RegexChunking(),
        markdown_generator: MarkdownGenerationStrategy = DefaultMarkdownGenerator(),
        only_text: bool = False,
        css_selector: str = None,
        target_elements: List[str] = None,
        excluded_tags: list = None,
        excluded_selector: str = None,
        keep_data_attributes: bool = False,
        keep_attrs: list = None,
        remove_forms: bool = False,
        prettiify: bool = False,
        parser_type: str = "lxml",
        scraping_strategy: ContentScrapingStrategy = None,
        proxy_config: Union["ProxyConfig", List["ProxyConfig"], dict, str, None] = None,
        proxy_rotation_strategy: Optional[ProxyRotationStrategy] = None,
        # Sticky Proxy Session Parameters
        proxy_session_id: Optional[str] = None,
        proxy_session_ttl: Optional[int] = None,
        proxy_session_auto_release: bool = False,
        # Browser Location and Identity Parameters
        locale: Optional[str] = None,
        timezone_id: Optional[str] = None,
        geolocation: Optional[GeolocationConfig] = None,
        # SSL Parameters
        fetch_ssl_certificate: bool = False,
        # Caching Parameters
        cache_mode: CacheMode = CacheMode.BYPASS,
        session_id: str = None,
        bypass_cache: bool = False,
        disable_cache: bool = False,
        no_cache_read: bool = False,
        no_cache_write: bool = False,
        shared_data: dict = None,
        # Cache Validation Parameters (Smart Cache)
        check_cache_freshness: bool = False,
        cache_validation_timeout: float = 10.0,
        # Page Navigation and Timing Parameters
        wait_until: str = "domcontentloaded",
        page_timeout: int = PAGE_TIMEOUT,
        wait_for: str = None,
        wait_for_timeout: int = None,
        wait_for_images: bool = False,
        delay_before_return_html: float = 0.1,
        mean_delay: float = 0.1,
        max_range: float = 0.3,
        semaphore_count: int = 5,
        # Page Interaction Parameters
        js_code: Union[str, List[str]] = None,
        js_code_before_wait: Union[str, List[str]] = None,
        c4a_script: Union[str, List[str]] = None,
        js_only: bool = False,
        ignore_body_visibility: bool = True,
        scan_full_page: bool = False,
        scroll_delay: float = 0.2,
        max_scroll_steps: Optional[int] = None,
        process_iframes: bool = False,
        flatten_shadow_dom: bool = False,
        remove_overlay_elements: bool = False,
        remove_consent_popups: bool = False,
        simulate_user: bool = False,
        override_navigator: bool = False,
        magic: bool = False,
        adjust_viewport_to_content: bool = False,
        # Media Handling Parameters
        screenshot: bool = False,
        screenshot_wait_for: float = None,
        screenshot_height_threshold: int = SCREENSHOT_HEIGHT_TRESHOLD,
        force_viewport_screenshot: bool = False,
        pdf: bool = False,
        capture_mhtml: bool = False,
        image_description_min_word_threshold: int = IMAGE_DESCRIPTION_MIN_WORD_THRESHOLD,
        image_score_threshold: int = IMAGE_SCORE_THRESHOLD,
        table_score_threshold: int = 7,
        table_extraction: TableExtractionStrategy = None,
        exclude_external_images: bool = False,
        exclude_all_images: bool = False,
        # Link and Domain Handling Parameters
        exclude_social_media_domains: list = None,
        exclude_external_links: bool = False,
        exclude_social_media_links: bool = False,
        exclude_domains: list = None,
        exclude_internal_links: bool = False,
        score_links: bool = False,
        preserve_https_for_internal_links: bool = False,
        # Debugging and Logging Parameters
        verbose: bool = True,
        log_console: bool = False,
        # Network and Console Capturing Parameters
        capture_network_requests: bool = False,
        capture_console_messages: bool = False,
        # Connection Parameters
        method: str = "GET",
        stream: bool = False,
        prefetch: bool = False,  # When True, return only HTML + links (skip heavy processing)
        process_in_browser: bool = False,  # Force browser processing for raw:/file:// URLs
        url: str = None,
        base_url: str = None,  # Base URL for markdown link resolution (used with raw: HTML)
        check_robots_txt: bool = False,
        user_agent: str = None,
        user_agent_mode: str = None,
        user_agent_generator_config: dict = {},
        # Deep Crawl Parameters
        deep_crawl_strategy: Optional[DeepCrawlStrategy] = None,
        # Link Extraction Parameters
        link_preview_config: Union[LinkPreviewConfig, Dict[str, Any]] = None,
        # Virtual Scroll Parameters
        virtual_scroll_config: Union[VirtualScrollConfig, Dict[str, Any]] = None,
        # URL Matching Parameters
        url_matcher: Optional[UrlMatcher] = None,
        match_mode: MatchMode = MatchMode.OR,
        # Experimental Parameters
        experimental: Dict[str, Any] = None,
        # Anti-Bot Retry Parameters
        max_retries: int = 0,
        fallback_fetch_function: Optional[Callable[[str], Awaitable[str]]] = None,
    ):
        # TODO: Planning to set properties dynamically based on the __init__ signature
        self.url = url
        self.base_url = base_url  # Base URL for markdown link resolution

        # Content Processing Parameters
        self.word_count_threshold = word_count_threshold
        self.extraction_strategy = extraction_strategy
        self.chunking_strategy = chunking_strategy
        self.markdown_generator = markdown_generator
        self.only_text = only_text
        self.css_selector = css_selector
        self.target_elements = target_elements or []
        self.excluded_tags = excluded_tags or []
        self.excluded_selector = excluded_selector or ""
        self.keep_data_attributes = keep_data_attributes
        self.keep_attrs = keep_attrs or []
        self.remove_forms = remove_forms
        self.prettiify = prettiify
        self.parser_type = parser_type
        self.scraping_strategy = scraping_strategy or LXMLWebScrapingStrategy()
        self.proxy_config = proxy_config  # runs through property setter

        self.proxy_rotation_strategy = proxy_rotation_strategy

        # Sticky Proxy Session Parameters
        self.proxy_session_id = proxy_session_id
        self.proxy_session_ttl = proxy_session_ttl
        self.proxy_session_auto_release = proxy_session_auto_release

        # Browser Location and Identity Parameters
        self.locale = locale
        self.timezone_id = timezone_id
        self.geolocation = geolocation

        # SSL Parameters
        self.fetch_ssl_certificate = fetch_ssl_certificate

        # Caching Parameters
        self.cache_mode = cache_mode
        self.session_id = session_id
        self.bypass_cache = bypass_cache
        self.disable_cache = disable_cache
        self.no_cache_read = no_cache_read
        self.no_cache_write = no_cache_write
        self.shared_data = shared_data
        # Cache Validation (Smart Cache)
        self.check_cache_freshness = check_cache_freshness
        self.cache_validation_timeout = cache_validation_timeout

        # Page Navigation and Timing Parameters
        self.wait_until = wait_until
        self.page_timeout = page_timeout
        self.wait_for = wait_for
        self.wait_for_timeout = wait_for_timeout
        self.wait_for_images = wait_for_images
        self.delay_before_return_html = delay_before_return_html
        self.mean_delay = mean_delay
        self.max_range = max_range
        self.semaphore_count = semaphore_count

        # Page Interaction Parameters
        self.js_code = js_code
        self.js_code_before_wait = js_code_before_wait
        self.c4a_script = c4a_script
        self.js_only = js_only
        self.ignore_body_visibility = ignore_body_visibility
        self.scan_full_page = scan_full_page
        self.scroll_delay = scroll_delay
        self.max_scroll_steps = max_scroll_steps
        self.process_iframes = process_iframes
        self.flatten_shadow_dom = flatten_shadow_dom
        self.remove_overlay_elements = remove_overlay_elements
        self.remove_consent_popups = remove_consent_popups
        self.simulate_user = simulate_user
        self.override_navigator = override_navigator
        self.magic = magic
        self.adjust_viewport_to_content = adjust_viewport_to_content

        # Media Handling Parameters
        self.screenshot = screenshot
        self.screenshot_wait_for = screenshot_wait_for
        self.screenshot_height_threshold = screenshot_height_threshold
        self.force_viewport_screenshot = force_viewport_screenshot
        self.pdf = pdf
        self.capture_mhtml = capture_mhtml
        self.image_description_min_word_threshold = image_description_min_word_threshold
        self.image_score_threshold = image_score_threshold
        self.exclude_external_images = exclude_external_images
        self.exclude_all_images = exclude_all_images
        self.table_score_threshold = table_score_threshold

        # Table extraction strategy (default to DefaultTableExtraction if not specified)
        if table_extraction is None:
            self.table_extraction = DefaultTableExtraction(table_score_threshold=table_score_threshold)
        else:
            self.table_extraction = table_extraction

        # Link and Domain Handling Parameters
        self.exclude_social_media_domains = (
            exclude_social_media_domains or SOCIAL_MEDIA_DOMAINS
        )
        self.exclude_external_links = exclude_external_links
        self.exclude_social_media_links = exclude_social_media_links
        self.exclude_domains = exclude_domains or []
        self.exclude_internal_links = exclude_internal_links
        self.score_links = score_links
        self.preserve_https_for_internal_links = preserve_https_for_internal_links

        # Debugging and Logging Parameters
        self.verbose = verbose
        self.log_console = log_console

        # Network and Console Capturing Parameters
        self.capture_network_requests = capture_network_requests
        self.capture_console_messages = capture_console_messages

        # Connection Parameters
        self.stream = stream
        self.prefetch = prefetch  # Prefetch mode: return only HTML + links
        self.process_in_browser = process_in_browser  # Force browser processing for raw:/file:// URLs
        self.method = method

        # Robots.txt Handling Parameters
        self.check_robots_txt = check_robots_txt

        # User Agent Parameters
        self.user_agent = user_agent
        self.user_agent_mode = user_agent_mode
        self.user_agent_generator_config = user_agent_generator_config

        # Validate type of extraction strategy and chunking strategy if they are provided
        if self.extraction_strategy is not None and not isinstance(
            self.extraction_strategy, ExtractionStrategy
        ):
            raise ValueError(
                "extraction_strategy must be an instance of ExtractionStrategy"
            )
        if self.chunking_strategy is not None and not isinstance(
            self.chunking_strategy, ChunkingStrategy
        ):
            raise ValueError(
                "chunking_strategy must be an instance of ChunkingStrategy"
            )
        if self.markdown_generator is not None and not isinstance(
            self.markdown_generator, MarkdownGenerationStrategy
        ):
            hint = ""
            if isinstance(self.markdown_generator, dict):
                hint = (
                    ' The JSON format must be {"type": "<ClassName>", "params": {...}}.'
                    ' Note: "params" is required — "options" or other keys are not recognized.'
                )
            raise ValueError(
                "markdown_generator must be an instance of MarkdownGenerationStrategy, "
                f"got {type(self.markdown_generator).__name__}.{hint}"
            )

        # Set default chunking strategy if None
        if self.chunking_strategy is None:
            self.chunking_strategy = RegexChunking()

        # Deep Crawl Parameters
        self.deep_crawl_strategy = deep_crawl_strategy

        # Link Extraction Parameters
        if link_preview_config is None:
            self.link_preview_config = None
        elif isinstance(link_preview_config, LinkPreviewConfig):
            self.link_preview_config = link_preview_config
        elif isinstance(link_preview_config, dict):
            # Convert dict to config object for backward compatibility
            self.link_preview_config = LinkPreviewConfig.from_dict(link_preview_config)
        else:
            raise ValueError("link_preview_config must be LinkPreviewConfig object or dict")

        # Virtual Scroll Parameters
        if virtual_scroll_config is None:
            self.virtual_scroll_config = None
        elif isinstance(virtual_scroll_config, VirtualScrollConfig):
            self.virtual_scroll_config = virtual_scroll_config
        elif isinstance(virtual_scroll_config, dict):
            # Convert dict to config object for backward compatibility
            self.virtual_scroll_config = VirtualScrollConfig.from_dict(virtual_scroll_config)
        else:
            raise ValueError("virtual_scroll_config must be VirtualScrollConfig object or dict")

        # URL Matching Parameters
        self.url_matcher = url_matcher
        self.match_mode = match_mode

        # Experimental Parameters
        self.experimental = experimental or {}

        # Anti-Bot Retry Parameters
        self.max_retries = max_retries
        self.fallback_fetch_function = fallback_fetch_function

        # Compile C4A scripts if provided
        if self.c4a_script and not self.js_code:
            self._compile_c4a_script()