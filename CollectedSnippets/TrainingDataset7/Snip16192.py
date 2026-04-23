def select2_ajax_wait(self, timeout=10):
        from selenium.common.exceptions import NoSuchElementException
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as ec

        yield
        with self.disable_implicit_wait():
            try:
                loading_element = self.selenium.find_element(
                    By.CSS_SELECTOR, "li.select2-results__option.loading-results"
                )
            except NoSuchElementException:
                pass
            else:
                self.wait_until(ec.staleness_of(loading_element), timeout=timeout)