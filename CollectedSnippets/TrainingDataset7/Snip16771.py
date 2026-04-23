def _get_HTML_inside_element_by_id(id_):
            return self.selenium.find_element(By.ID, id_).get_attribute("innerHTML")