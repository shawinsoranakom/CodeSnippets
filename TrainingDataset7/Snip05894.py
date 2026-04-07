def wait_page_ready(self, timeout=10):
        """
        Block until the page is ready.
        """
        self.wait_until(
            lambda driver: driver.execute_script("return document.readyState;")
            == "complete",
            timeout,
        )