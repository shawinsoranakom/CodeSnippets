def deselect_option(self, selector, value):
        """
        Deselect the <OPTION> with the value `value` inside the <SELECT> widget
        identified by the CSS selector `selector`.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select

        select = Select(self.selenium.find_element(By.CSS_SELECTOR, selector))
        select.deselect_by_value(value)