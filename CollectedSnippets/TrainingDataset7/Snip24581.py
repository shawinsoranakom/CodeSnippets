def test13_select_related_null_fk(self):
        "Testing `select_related` on a nullable ForeignKey."
        Book.objects.create(title="Without Author")
        b = Book.objects.select_related("author").get(title="Without Author")
        # Should be `None`, and not a 'dummy' model.
        self.assertIsNone(b.author)