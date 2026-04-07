def test_readonly_manytomany_forwards_ref(self):
        topping = Topping.objects.create(name="Salami")
        pizza = Pizza.objects.create(name="Americano")
        pizza.toppings.add(topping)
        response = self.client.get(
            reverse("admin:admin_views_pizza_change", args=(pizza.pk,))
        )
        self.assertContains(response, "<label>Toppings:</label>", html=True)
        self.assertContains(response, '<div class="readonly">Salami</div>', html=True)