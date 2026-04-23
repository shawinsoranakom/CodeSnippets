def test_object_tools(self):
        from selenium.webdriver.common.by import By

        state = State.objects.create(name="Korea")
        city = City.objects.create(state=state, name="Gwangju")
        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_views_city_changelist")
        )
        object_tools = self.selenium.find_elements(
            By.CSS_SELECTOR, "ul.object-tools li a"
        )
        self.assertEqual(len(object_tools), 1)
        self.take_screenshot("changelist")

        self.selenium.get(
            self.live_server_url
            + reverse("admin:admin_views_city_change", args=(city.pk,))
        )
        object_tools = self.selenium.find_elements(
            By.CSS_SELECTOR, "ul.object-tools li a"
        )
        self.assertEqual(len(object_tools), 2)
        self.take_screenshot("changeform")