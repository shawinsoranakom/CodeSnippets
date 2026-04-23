def test_related_object_lookup_link_initial_state(self):
        from selenium.webdriver.common.by import By

        album_add_url = reverse("admin:admin_views_album_add")
        self.selenium.get(self.live_server_url + album_add_url)

        tests = [
            "change_id_owner",
            "delete_id_owner",
            "view_id_owner",
        ]
        for link_id in tests:
            with self.subTest(link_id):
                link = self.selenium.find_element(By.XPATH, f'//*[@id="{link_id}"]')
                self.assertEqual(link.get_attribute("aria-disabled"), "true")