def test_label_suffix_translated(self):
        pizza = Pizza.objects.create(name="Americano")
        url = reverse("admin:admin_views_pizza_change", args=(pizza.pk,))
        with self.settings(LANGUAGE_CODE="fr"):
            response = self.client.get(url)
        self.assertContains(response, "<label>Toppings\u00a0:</label>", html=True)