def test_cancel_delete_confirmation(self):
        "Cancelling the deletion of an object takes the user back one page."
        from selenium.webdriver.common.by import By

        pizza = Pizza.objects.create(name="Double Cheese")
        url = reverse("admin:admin_views_pizza_change", args=(pizza.id,))
        full_url = self.live_server_url + url
        self.admin_login(
            username="super", password="secret", login_url=reverse("admin:index")
        )
        self.selenium.get(full_url)
        self.selenium.find_element(By.CLASS_NAME, "deletelink").click()
        # Click 'cancel' on the delete page.
        self.selenium.find_element(By.CLASS_NAME, "cancel-link").click()
        # Wait until we're back on the change page.
        self.wait_for_text("#content h1", "Change pizza")
        self.assertEqual(self.selenium.current_url, full_url)
        self.assertEqual(Pizza.objects.count(), 1)