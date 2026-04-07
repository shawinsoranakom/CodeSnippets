def test_values_alias(self):
        qs = Book.objects.alias(rating_alias=F("rating") - 1)
        msg = "Cannot select the 'rating_alias' alias. Use annotate() to promote it."
        for operation in ["values", "values_list"]:
            with self.subTest(operation=operation):
                with self.assertRaisesMessage(FieldError, msg):
                    getattr(qs, operation)("rating_alias")