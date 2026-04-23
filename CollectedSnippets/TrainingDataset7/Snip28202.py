def test_field_str(self):
        f = models.Field()
        self.assertEqual(str(f), "<django.db.models.fields.Field>")
        f = Foo._meta.get_field("a")
        self.assertEqual(str(f), "model_fields.Foo.a")