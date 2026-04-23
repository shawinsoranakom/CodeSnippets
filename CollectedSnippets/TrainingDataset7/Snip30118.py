def test_unknown(self):
        book1 = Book.objects.get(id=self.book1.id)
        with self.assertRaises(AttributeError):
            prefetch_related_objects([book1], "unknown_attribute")