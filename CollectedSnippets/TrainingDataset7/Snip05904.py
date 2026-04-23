def is_disabled(self, selector):
        """
        Return True if the element identified by `selector` has the `disabled`
        attribute.
        """
        from selenium.webdriver.common.by import By

        return (
            self.selenium.find_element(By.CSS_SELECTOR, selector).get_attribute(
                "disabled"
            )
            == "true"
        )