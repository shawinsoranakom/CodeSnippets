def _submit_and_wait(self):
        from selenium.webdriver.common.by import By

        with self.wait_page_loaded():
            self.selenium.find_element(
                By.CSS_SELECTOR, "input[value='Save and continue editing']"
            ).click()