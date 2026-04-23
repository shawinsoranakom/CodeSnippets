def test_skip_link_keyboard_navigation_in_changelist(self):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys

        Podcast.objects.create(name="apple", release_date="2000-09-19")
        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        self.selenium.get(
            self.live_server_url + reverse("admin:admin_views_podcast_changelist")
        )
        selectors = [
            "ul.object-tools",  # object_tools.
            "search#changelist-filter",  # list_filter.
            "form#changelist-search",  # search_fields.
            "nav.toplinks",  # date_hierarchy.
            "form#changelist-form div.actions",  # action.
            "table#result_list",  # table.
            "div.changelist-footer",  # footer.
        ]
        content = self.selenium.find_element(By.ID, "content-start")
        content.send_keys(Keys.TAB)

        for selector in selectors:
            with self.subTest(selector=selector):
                # Currently focused element.
                focused_element = self.selenium.switch_to.active_element
                expected_element = self.selenium.find_element(By.CSS_SELECTOR, selector)
                element_points = self.selenium.find_elements(
                    By.CSS_SELECTOR,
                    f"{selector} a, {selector} input, {selector} button",
                )
                self.assertIn(
                    focused_element.get_attribute("outerHTML"),
                    expected_element.get_attribute("innerHTML"),
                )
                # Move to the next container element via TAB.
                for point in element_points[::-1]:
                    if point.is_displayed():
                        point.send_keys(Keys.TAB)
                        break