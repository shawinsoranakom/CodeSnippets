def test_tabular_inline_object_with_show_change_link(self):
        from selenium.webdriver.common.by import By

        et = ExtraTerrestrial.objects.create(name="test")
        Sighting.objects.create(et=et, place="Desert")
        self.admin_login(username="super", password="secret")
        url = reverse("admin:admin_inlines_extraterrestrial_change", args=(et.pk,))
        self.selenium.get(self.live_server_url + url)
        object_str = self.selenium.find_element(
            By.CSS_SELECTOR, "fieldset.module tbody tr td.original p"
        )
        self.assertTrue(object_str.is_displayed())
        self.assertIn("Desert", object_str.text)
        self.take_screenshot("tabular")