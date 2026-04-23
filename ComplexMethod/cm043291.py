def get_browser_stack(self, num_browsers: int = 1) -> List[str]:
        """
        Get a valid combination of browser versions.

        How it works:
        1. Check if the number of browsers is supported.
        2. Randomly choose a combination of browsers.
        3. Iterate through the combination and add browser versions.
        4. Return the browser stack.

        Args:
            num_browsers: Number of browser specifications (1-3)

        Returns:
            List[str]: A list of browser versions.
        """
        if num_browsers not in self.browser_combinations:
            raise ValueError(f"Unsupported number of browsers: {num_browsers}")

        combination = random.choice(self.browser_combinations[num_browsers])
        browser_stack = []

        for browser in combination:
            if browser == "chrome":
                browser_stack.append(random.choice(self.chrome_versions))
            elif browser == "firefox":
                browser_stack.append(random.choice(self.firefox_versions))
            elif browser == "safari":
                browser_stack.append(random.choice(self.safari_versions))
            elif browser == "edge":
                browser_stack.append(random.choice(self.edge_versions))
            elif browser == "gecko":
                browser_stack.append(random.choice(self.rendering_engines["gecko"]))
            elif browser == "webkit":
                browser_stack.append(self.rendering_engines["chrome_webkit"])

        return browser_stack