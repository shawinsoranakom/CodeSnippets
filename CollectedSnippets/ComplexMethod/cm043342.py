async def create_browser_context(self, crawlerRunConfig: CrawlerRunConfig = None):
        """
        Creates and returns a new browser context with configured settings.
        Applies text-only mode settings if text_mode is enabled in config.

        Returns:
            Context: Browser context object with the specified configurations
        """
        if self.browser is None:
            if self._launched_persistent:
                raise RuntimeError(
                    "Cannot create new browser contexts when using "
                    "use_persistent_context=True. Persistent context uses a "
                    "single shared context."
                )
            raise RuntimeError(
                "Browser is not available. It may have been closed, crashed, "
                "or not yet started. Ensure the browser is running before "
                "creating new contexts."
            )
        # Base settings
        user_agent = self.config.headers.get("User-Agent", self.config.user_agent) 
        viewport_settings = {
            "width": self.config.viewport_width,
            "height": self.config.viewport_height,
        }
        proxy_settings = {"server": self.config.proxy} if self.config.proxy else None

        # CSS extensions (blocked separately via avoid_css flag)
        css_extensions = ["css", "less", "scss", "sass"]

        # Static resource extensions (blocked when text_mode is enabled)
        static_extensions = [
            # Images
            "jpg", "jpeg", "png", "gif", "webp", "svg", "ico", "bmp", "tiff", "psd",
            # Fonts
            "woff", "woff2", "ttf", "otf", "eot",
            # Media
            "mp4", "webm", "ogg", "avi", "mov", "wmv", "flv", "m4v",
            "mp3", "wav", "aac", "m4a", "opus", "flac",
            # Documents
            "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
            # Archives
            "zip", "rar", "7z", "tar", "gz",
            # Scripts and data
            "xml", "swf", "wasm",
        ]

        # Ad and tracker domain patterns (curated from uBlock/EasyList sources)
        ad_tracker_patterns = [
            "**/google-analytics.com/**",
            "**/googletagmanager.com/**",
            "**/googlesyndication.com/**",
            "**/doubleclick.net/**",
            "**/adservice.google.com/**",
            "**/adsystem.com/**",
            "**/adzerk.net/**",
            "**/adnxs.com/**",
            "**/ads.linkedin.com/**",
            "**/facebook.net/**",
            "**/analytics.twitter.com/**",
            "**/ads-twitter.com/**",
            "**/hotjar.com/**",
            "**/clarity.ms/**",
            "**/scorecardresearch.com/**",
            "**/pixel.wp.com/**",
            "**/amazon-adsystem.com/**",
            "**/mixpanel.com/**",
            "**/segment.com/**",
        ]

        # Common context settings
        context_settings = {
            "user_agent": user_agent,
            "viewport": viewport_settings,
            "proxy": proxy_settings,
            "accept_downloads": self.config.accept_downloads,
            "storage_state": self.config.storage_state,
            "ignore_https_errors": self.config.ignore_https_errors,
            "device_scale_factor": self.config.device_scale_factor,
            "java_script_enabled": self.config.java_script_enabled,
        }

        if crawlerRunConfig:
            # Check if there is value for crawlerRunConfig.proxy_config set add that to context
            if crawlerRunConfig.proxy_config:
                from playwright.async_api import ProxySettings
                proxy_settings = ProxySettings(
                    server=crawlerRunConfig.proxy_config.server,
                    username=crawlerRunConfig.proxy_config.username,
                    password=crawlerRunConfig.proxy_config.password,
                )
                context_settings["proxy"] = proxy_settings

        if self.config.text_mode:
            text_mode_settings = {
                "has_touch": False,
                "is_mobile": False,
            }
            # Update context settings with text mode settings
            context_settings.update(text_mode_settings)

        # inject locale / tz / geo if user provided them
        if crawlerRunConfig:
            if crawlerRunConfig.locale:
                context_settings["locale"] = crawlerRunConfig.locale
            if crawlerRunConfig.timezone_id:
                context_settings["timezone_id"] = crawlerRunConfig.timezone_id
            if crawlerRunConfig.geolocation:
                context_settings["geolocation"] = {
                    "latitude": crawlerRunConfig.geolocation.latitude,
                    "longitude": crawlerRunConfig.geolocation.longitude,
                    "accuracy": crawlerRunConfig.geolocation.accuracy,
                }
                # ensure geolocation permission
                perms = context_settings.get("permissions", [])
                perms.append("geolocation")
                context_settings["permissions"] = perms

        # Create and return the context with all settings
        context = await self.browser.new_context(**context_settings)

        # Build dynamic blocking list based on config flags
        to_block = []
        if self.config.avoid_css:
            to_block.extend(css_extensions)
        if self.config.text_mode:
            to_block.extend(static_extensions)

        if to_block:
            for ext in to_block:
                await context.route(f"**/*.{ext}", lambda route: route.abort())

        if self.config.avoid_ads:
            for pattern in ad_tracker_patterns:
                await context.route(pattern, lambda route: route.abort())

        return context