def generate(
        self,
        device_type: Optional[Literal["desktop", "mobile"]] = None,
        os_type: Optional[str] = None,
        device_brand: Optional[str] = None,
        browser_type: Optional[Literal["chrome", "edge", "safari", "firefox"]] = None,
        num_browsers: int = 3,
    ) -> str:
        """
        Generate a random user agent with specified constraints.

        Args:
            device_type: 'desktop' or 'mobile'
            os_type: 'windows', 'macos', 'linux', 'android', 'ios'
            device_brand: Specific device brand
            browser_type: 'chrome', 'edge', 'safari', or 'firefox'
            num_browsers: Number of browser specifications (1-3)
        """
        # Get platform string
        platform = self.get_random_platform(device_type, os_type, device_brand)

        # Start with Mozilla
        components = ["Mozilla/5.0", platform]

        # Add browser stack
        browser_stack = self.get_browser_stack(num_browsers)

        # Add appropriate legacy token based on browser stack
        if "Firefox" in str(browser_stack) or browser_type == "firefox":
            components.append(random.choice(self.rendering_engines["gecko"]))
        elif "Chrome" in str(browser_stack) or "Safari" in str(browser_stack) or browser_type == "chrome":
            components.append(self.rendering_engines["chrome_webkit"])
            components.append("(KHTML, like Gecko)")
        elif "Edge" in str(browser_stack) or browser_type == "edge":
            components.append(self.rendering_engines["safari_webkit"])
            components.append("(KHTML, like Gecko)")
        elif "Safari" in str(browser_stack) or browser_type == "safari":
            components.append(self.rendering_engines["chrome_webkit"])
            components.append("(KHTML, like Gecko)")

        # Add browser versions
        components.extend(browser_stack)

        return " ".join(components)