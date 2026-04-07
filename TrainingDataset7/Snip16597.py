def test_pagination_layout(self):
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        objects = [UnorderedObject(name=f"obj-{i}") for i in range(1, 23)]
        UnorderedObject.objects.bulk_create(objects)
        self.selenium.get(
            self.live_server_url
            + reverse("admin:admin_views_unorderedobject_changelist")
        )
        pages = self.selenium.find_elements(By.CSS_SELECTOR, "nav.paginator ul li")
        self.assertGreater(len(pages), 1)
        show_all = self.selenium.find_element(By.CSS_SELECTOR, "a.showall")
        self.assertTrue(show_all.is_displayed())
        self.take_screenshot("pagination")