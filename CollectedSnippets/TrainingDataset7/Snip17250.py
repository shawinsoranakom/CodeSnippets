def test_defer_only_alias(self):
        qs = Book.objects.alias(rating_alias=F("rating") - 1)
        msg = "Book has no field named 'rating_alias'"
        for operation in ["defer", "only"]:
            with self.subTest(operation=operation):
                with self.assertRaisesMessage(FieldDoesNotExist, msg):
                    getattr(qs, operation)("rating_alias").first()