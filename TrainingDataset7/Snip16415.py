def test_delete_view_with_no_default_permissions(self):
        """
        The delete view allows users to delete collected objects without a
        'delete' permission (ReadOnlyPizza.Meta.default_permissions is empty).
        """
        pizza = ReadOnlyPizza.objects.create(name="Double Cheese")
        delete_url = reverse("admin:admin_views_readonlypizza_delete", args=(pizza.pk,))
        self.client.force_login(self.adduser)
        response = self.client.get(delete_url)
        self.assertContains(response, "admin_views/readonlypizza/%s/" % pizza.pk)
        self.assertContains(response, "<h2>Summary</h2>")
        self.assertContains(response, "<li>Read only pizzas: 1</li>")
        post = self.client.post(delete_url, {"post": "yes"})
        self.assertRedirects(
            post, reverse("admin:admin_views_readonlypizza_changelist")
        )
        self.assertEqual(ReadOnlyPizza.objects.count(), 0)