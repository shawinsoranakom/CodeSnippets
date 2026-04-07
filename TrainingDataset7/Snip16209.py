def test_pagination(self):
        from selenium.webdriver.common.by import By

        user_history_url = reverse("admin:auth_user_history", args=(self.superuser.pk,))
        self.selenium.get(self.live_server_url + user_history_url)

        paginator = self.selenium.find_element(By.CSS_SELECTOR, ".paginator")
        self.assertEqual(paginator.tag_name, "nav")
        labelledby = paginator.get_attribute("aria-labelledby")
        description = self.selenium.find_element(By.CSS_SELECTOR, "#%s" % labelledby)
        self.assertHTMLEqual(
            description.get_attribute("outerHTML"),
            '<h2 id="pagination" class="visually-hidden">Pagination user entries</h2>',
        )
        self.assertTrue(paginator.is_displayed())
        aria_current_link = paginator.find_elements(By.CSS_SELECTOR, "[aria-current]")
        self.assertEqual(len(aria_current_link), 1)
        # The current page.
        current_page_link = aria_current_link[0]
        self.assertEqual(current_page_link.get_attribute("aria-current"), "page")
        self.assertEqual(current_page_link.get_attribute("href"), "")
        self.assertIn("%s entries" % LogEntry.objects.count(), paginator.text)
        self.assertIn(str(Paginator.ELLIPSIS), paginator.text)
        self.assertEqual(current_page_link.text, "1")
        # The last page.
        last_page_link = self.selenium.find_element(By.XPATH, "//ul/li[last()]/a")
        self.assertTrue(last_page_link.text, "20")
        # Select the second page.
        pages = paginator.find_elements(By.TAG_NAME, "a")
        second_page_link = pages[1]
        self.assertEqual(second_page_link.text, "2")
        second_page_link.click()
        self.assertIn("?p=2", self.selenium.current_url)
        rows = self.selenium.find_elements(By.CSS_SELECTOR, "#change-history tbody tr")
        self.assertIn("Changed something 101", rows[0].text)
        self.assertIn("Changed something 200", rows[-1].text)