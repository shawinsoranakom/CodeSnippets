async def smart_wait(self, page: Page, wait_for: str, timeout: float = 30000):
        """
        Wait for a condition in a smart way. This functions works as below:

        1. If wait_for starts with 'js:', it assumes it's a JavaScript function and waits for it to return true.
        2. If wait_for starts with 'css:', it assumes it's a CSS selector and waits for it to be present.
        3. Otherwise, it tries to evaluate wait_for as a JavaScript function and waits for it to return true.
        4. If it's not a JavaScript function, it assumes it's a CSS selector and waits for it to be present.

        This is a more advanced version of the wait_for parameter in CrawlerStrategy.crawl().
        Args:
            page: Playwright page object
            wait_for (str): The condition to wait for. Can be a CSS selector, a JavaScript function, or explicitly prefixed with 'js:' or 'css:'.
            timeout (float): Maximum time to wait in milliseconds

        Returns:
            None
        """
        wait_for = wait_for.strip()

        if wait_for.startswith("js:"):
            # Explicitly specified JavaScript
            js_code = wait_for[3:].strip()
            return await self.csp_compliant_wait(page, js_code, timeout)
        elif wait_for.startswith("css:"):
            # Explicitly specified CSS selector
            css_selector = wait_for[4:].strip()
            try:
                await page.wait_for_selector(css_selector, timeout=timeout)
            except Error as e:
                if "Timeout" in str(e):
                    raise TimeoutError(
                        f"Timeout after {timeout}ms waiting for selector '{css_selector}'"
                    )
                else:
                    raise ValueError(f"Invalid CSS selector: '{css_selector}'")
        else:
            # Auto-detect based on content
            if wait_for.startswith("()") or wait_for.startswith("function"):
                # It's likely a JavaScript function
                return await self.csp_compliant_wait(page, wait_for, timeout)
            else:
                # Assume it's a CSS selector first
                try:
                    await page.wait_for_selector(wait_for, timeout=timeout)
                except Error as e:
                    if "Timeout" in str(e):
                        raise TimeoutError(
                            f"Timeout after {timeout}ms waiting for selector '{wait_for}'"
                        )
                    else:
                        # If it's not a timeout error, it might be an invalid selector
                        # Let's try to evaluate it as a JavaScript function as a fallback
                        try:
                            return await self.csp_compliant_wait(
                                page, f"() => {{{wait_for}}}", timeout
                            )
                        except Error:
                            raise ValueError(
                                f"Invalid wait_for parameter: '{wait_for}'. "
                                "It should be either a valid CSS selector, a JavaScript function, "
                                "or explicitly prefixed with 'js:' or 'css:'."
                            )