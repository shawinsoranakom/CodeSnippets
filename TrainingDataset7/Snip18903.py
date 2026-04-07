def test_auto_field_with_value_refreshed(self):
        """
        An auto field must be refreshed by Model.save() even when a value is
        set because the database may return a value of a different type.
        """
        a = Article.objects.create(pk="123456", pub_date=datetime(2025, 9, 16))
        self.assertEqual(a.pk, 123456)