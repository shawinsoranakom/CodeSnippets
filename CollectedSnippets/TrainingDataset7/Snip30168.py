def test_invalid_final_lookup(self):
        qs = Book.objects.prefetch_related("authors__name")
        msg = (
            "'authors__name' does not resolve to an item that supports "
            "prefetching - this is an invalid parameter to prefetch_related()."
        )
        with self.assertRaisesMessage(ValueError, msg) as cm:
            list(qs)

        self.assertIn("prefetch_related", str(cm.exception))
        self.assertIn("name", str(cm.exception))