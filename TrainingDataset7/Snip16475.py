def test_shortcut_view_with_escaping(self):
        "'View on site should' work properly with char fields"
        model = ModelWithStringPrimaryKey(pk="abc_123")
        model.save()
        response = self.client.get(
            reverse(
                "admin:admin_views_modelwithstringprimarykey_change",
                args=(quote(model.pk),),
            )
        )
        should_contain = '/%s/" class="viewsitelink">' % model.pk
        self.assertContains(response, should_contain)