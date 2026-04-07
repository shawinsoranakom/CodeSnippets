def test_url_conflicts_with_history(self):
        "A model with a primary key that ends with history should be visible"
        history_model = ModelWithStringPrimaryKey(pk="history")
        history_model.save()
        response = self.client.get(
            reverse(
                "admin:admin_views_modelwithstringprimarykey_change",
                args=(quote(history_model.pk),),
            )
        )
        should_contain = """<h1>Change model with string primary key</h1>"""
        self.assertContains(response, should_contain)