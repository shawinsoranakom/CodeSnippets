def test_attribute_error(self):
        qs = Reader.objects.prefetch_related("books_read__xyz")
        msg = (
            "Cannot find 'xyz' on Book object, 'books_read__xyz' "
            "is an invalid parameter to prefetch_related()"
        )
        with self.assertRaisesMessage(AttributeError, msg) as cm:
            list(qs)

        self.assertIn("prefetch_related", str(cm.exception))