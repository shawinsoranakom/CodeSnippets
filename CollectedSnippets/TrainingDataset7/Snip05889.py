def wait_for(self, css_selector, timeout=10):
        """
        Block until a CSS selector is found on the page.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as ec

        self.wait_until(
            ec.presence_of_element_located((By.CSS_SELECTOR, css_selector)), timeout
        )