def wait_page_loaded(self, timeout=10):
        """
        Block until a new page has loaded and is ready.
        """
        from selenium.common.exceptions import WebDriverException
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as ec

        old_page = self.selenium.find_element(By.TAG_NAME, "html")
        yield
        # Wait for the next page to be loaded
        try:
            self.wait_until(ec.staleness_of(old_page), timeout=timeout)
        except WebDriverException:
            # Issue in version 113+ of Chrome driver where a WebDriverException
            # error is raised rather than a StaleElementReferenceException.
            # See: https://issues.chromium.org/issues/42323468
            pass

        self.wait_page_ready(timeout=timeout)