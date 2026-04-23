async def test_bot_detection(use_stealth: bool = False) -> Dict[str, Any]:
    """Test against a bot detection service"""

    logger.info(
        f"Testing bot detection with stealth={'ON' if use_stealth else 'OFF'}",
        tag="STEALTH"
    )

    # Configure browser with or without stealth
    browser_config = BrowserConfig(
        headless=False,  # Use False to see the browser in action
        enable_stealth=use_stealth,
        viewport_width=1280,
        viewport_height=800
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        # JavaScript to extract bot detection results
        detection_script = """
        // Comprehensive bot detection checks
        (() => {
        const detectionResults = {
            // Basic WebDriver detection
            webdriver: navigator.webdriver,

            // Chrome specific
            chrome: !!window.chrome,
            chromeRuntime: !!window.chrome?.runtime,

            // Automation indicators
            automationControlled: navigator.webdriver,

            // Permissions API
            permissionsPresent: !!navigator.permissions?.query,

            // Plugins
            pluginsLength: navigator.plugins.length,
            pluginsArray: Array.from(navigator.plugins).map(p => p.name),

            // Languages
            languages: navigator.languages,
            language: navigator.language,

            // User agent
            userAgent: navigator.userAgent,

            // Screen and window properties
            screen: {
                width: screen.width,
                height: screen.height,
                availWidth: screen.availWidth,
                availHeight: screen.availHeight,
                colorDepth: screen.colorDepth,
                pixelDepth: screen.pixelDepth
            },

            // WebGL vendor
            webglVendor: (() => {
                try {
                    const canvas = document.createElement('canvas');
                    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                    const ext = gl.getExtension('WEBGL_debug_renderer_info');
                    return gl.getParameter(ext.UNMASKED_VENDOR_WEBGL);
                } catch (e) {
                    return 'Error';
                }
            })(),

            // Platform
            platform: navigator.platform,

            // Hardware concurrency
            hardwareConcurrency: navigator.hardwareConcurrency,

            // Device memory
            deviceMemory: navigator.deviceMemory,

            // Connection
            connection: navigator.connection?.effectiveType
        };

        // Log results for console capture
        console.log('DETECTION_RESULTS:', JSON.stringify(detectionResults, null, 2));

        // Return results
        return detectionResults;
        })();
        """

        # Crawl bot detection test page
        config = CrawlerRunConfig(
            js_code=detection_script,
            capture_console_messages=True,
            wait_until="networkidle",
            delay_before_return_html=2.0  # Give time for all checks to complete
        )

        result = await crawler.arun(
            url="https://bot.sannysoft.com",
            config=config
        )

        if result.success:
            # Extract detection results from console
            detection_data = None
            for msg in result.console_messages or []:
                if "DETECTION_RESULTS:" in msg.get("text", ""):
                    try:
                        json_str = msg["text"].replace("DETECTION_RESULTS:", "").strip()
                        detection_data = json.loads(json_str)
                    except:
                        pass

            # Also try to get from JavaScript execution result
            if not detection_data and result.js_execution_result:
                detection_data = result.js_execution_result

            return {
                "success": True,
                "url": result.url,
                "detection_data": detection_data,
                "page_title": result.metadata.get("title", ""),
                "stealth_enabled": use_stealth
            }
        else:
            return {
                "success": False,
                "error": result.error_message,
                "stealth_enabled": use_stealth
            }