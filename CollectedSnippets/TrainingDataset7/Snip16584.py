def test_search_input_filtered_page(self):
        from selenium.webdriver.common.by import By

        Person.objects.create(name="Guido van Rossum", gender=1, alive=True)
        Person.objects.create(name="Grace Hopper", gender=1, alive=False)
        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        person_url = reverse("admin:admin_views_person_changelist") + "?q=Gui"
        self.selenium.get(self.live_server_url + person_url)
        # Hide sidebar.
        toggle_button = self.selenium.find_element(
            By.CSS_SELECTOR, "#toggle-nav-sidebar"
        )
        toggle_button.click()
        self.addCleanup(_clean_sidebar_state, self.selenium)
        self.assertGreater(
            self.selenium.find_element(By.ID, "searchbar").rect["width"],
            50,
        )