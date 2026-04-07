def test_field_repr(self):
        """
        __repr__() of a field displays its name.
        """
        f = Foo._meta.get_field("a")
        self.assertEqual(repr(f), "<django.db.models.fields.CharField: a>")
        f = models.fields.CharField()
        self.assertEqual(repr(f), "<django.db.models.fields.CharField>")