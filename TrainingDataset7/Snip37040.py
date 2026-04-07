def test_multiple_catalogs(self):
        from selenium.webdriver.common.by import By

        self.selenium.get(self.live_server_url + "/jsi18n_multi_catalogs/")
        elem = self.selenium.find_element(By.ID, "app1string")
        self.assertEqual(
            elem.text, "il faut traduire cette chaîne de caractères de app1"
        )
        elem = self.selenium.find_element(By.ID, "app2string")
        self.assertEqual(
            elem.text, "il faut traduire cette chaîne de caractères de app2"
        )