def test_changelist_filter_sidebar_with_long_verbose_fields(self):
        from selenium.webdriver.common.by import By

        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        Person.objects.create(name="John", gender=1)
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_views_person_changelist")
        )
        changelist_filter = self.selenium.find_element(By.ID, "changelist-filter")
        self.assertTrue(changelist_filter.is_displayed())
        self.take_screenshot("filter_sidebar")