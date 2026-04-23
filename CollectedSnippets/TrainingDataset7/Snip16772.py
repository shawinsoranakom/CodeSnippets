def _get_text_inside_element_by_selector(selector):
            return self.selenium.find_element(By.CSS_SELECTOR, selector).get_attribute(
                "innerText"
            )