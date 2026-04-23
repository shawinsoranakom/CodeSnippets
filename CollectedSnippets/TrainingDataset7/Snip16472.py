def test_url_conflicts_with_add(self):
        """
        A model with a primary key that ends with add or is `add` should be
        visible
        """
        add_model = ModelWithStringPrimaryKey.objects.create(
            pk="i have something to add"
        )
        add_model.save()
        response = self.client.get(
            reverse(
                "admin:admin_views_modelwithstringprimarykey_change",
                args=(quote(add_model.pk),),
            )
        )
        should_contain = """<h1>Change model with string primary key</h1>"""
        self.assertContains(response, should_contain)

        add_model2 = ModelWithStringPrimaryKey.objects.create(pk="add")
        add_url = reverse("admin:admin_views_modelwithstringprimarykey_add")
        change_url = reverse(
            "admin:admin_views_modelwithstringprimarykey_change",
            args=(quote(add_model2.pk),),
        )
        self.assertNotEqual(add_url, change_url)