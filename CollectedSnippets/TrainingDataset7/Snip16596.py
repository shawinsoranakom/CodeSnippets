def test_long_header_with_object_tools_layout(self):
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        s = Subscriber.objects.create(name="a " * 40, email="b " * 80)
        self.selenium.get(
            self.live_server_url
            + reverse("admin:admin_views_subscriber_change", args=(s.pk,))
        )
        header = self.selenium.find_element(By.CSS_SELECTOR, "div#content h2")
        self.assertGreater(len(header.text), 100)
        object_tools = self.selenium.find_elements(
            By.CSS_SELECTOR, "div#content ul.object-tools li"
        )
        self.assertGreater(len(object_tools), 0)
        self.take_screenshot("change_form")

        self.selenium.get(
            self.live_server_url + reverse("admin:admin_views_restaurant_changelist")
        )
        header = self.selenium.find_element(By.CSS_SELECTOR, "div#content h1")
        self.assertGreater(len(header.text), 100)
        object_tools = self.selenium.find_elements(
            By.CSS_SELECTOR, "div#content ul.object-tools li"
        )
        self.assertGreater(len(object_tools), 0)
        self.take_screenshot("change_list")