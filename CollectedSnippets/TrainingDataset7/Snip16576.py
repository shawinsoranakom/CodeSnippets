def test_cancel_delete_related_confirmation(self):
        """
        Cancelling the deletion of an object with relations takes the user back
        one page.
        """
        from selenium.webdriver.common.by import By

        pizza = Pizza.objects.create(name="Double Cheese")
        topping1 = Topping.objects.create(name="Cheddar")
        topping2 = Topping.objects.create(name="Mozzarella")
        pizza.toppings.add(topping1, topping2)
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
        self.assertEqual(Topping.objects.count(), 2)