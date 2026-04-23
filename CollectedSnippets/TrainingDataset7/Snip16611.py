def test_readonly_manytomany_backwards_ref(self):
        """
        Regression test for #16433 - backwards references for related objects
        broke if the related field is read-only due to the help_text attribute
        """
        topping = Topping.objects.create(name="Salami")
        pizza = Pizza.objects.create(name="Americano")
        pizza.toppings.add(topping)
        response = self.client.get(reverse("admin:admin_views_topping_add"))
        self.assertEqual(response.status_code, 200)