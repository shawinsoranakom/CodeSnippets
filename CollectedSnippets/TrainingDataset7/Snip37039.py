def test_javascript_gettext(self):
        from selenium.webdriver.common.by import By

        self.selenium.get(self.live_server_url + "/jsi18n_template/")
        elem = self.selenium.find_element(By.ID, "gettext")
        self.assertEqual(elem.text, "Entfernen")
        elem = self.selenium.find_element(By.ID, "ngettext_sing")
        self.assertEqual(elem.text, "1 Element")
        elem = self.selenium.find_element(By.ID, "ngettext_plur")
        self.assertEqual(elem.text, "455 Elemente")
        elem = self.selenium.find_element(By.ID, "ngettext_onnonplural")
        self.assertEqual(elem.text, "Bild")
        elem = self.selenium.find_element(By.ID, "pgettext")
        self.assertEqual(elem.text, "Kann")
        elem = self.selenium.find_element(By.ID, "npgettext_sing")
        self.assertEqual(elem.text, "1 Resultat")
        elem = self.selenium.find_element(By.ID, "npgettext_plur")
        self.assertEqual(elem.text, "455 Resultate")
        elem = self.selenium.find_element(By.ID, "formats")
        self.assertEqual(
            elem.text,
            "DATE_INPUT_FORMATS is an object; DECIMAL_SEPARATOR is a string; "
            "FIRST_DAY_OF_WEEK is a number;",
        )