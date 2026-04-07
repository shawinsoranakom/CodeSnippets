def test_url_conflicts_with_delete(self):
        "A model with a primary key that ends with delete should be visible"
        delete_model = ModelWithStringPrimaryKey(pk="delete")
        delete_model.save()
        response = self.client.get(
            reverse(
                "admin:admin_views_modelwithstringprimarykey_change",
                args=(quote(delete_model.pk),),
            )
        )
        should_contain = """<h1>Change model with string primary key</h1>"""
        self.assertContains(response, should_contain)