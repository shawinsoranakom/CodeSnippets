def test_distinct_on_alias(self):
        qs = Book.objects.alias(rating_alias=F("rating") - 1)
        msg = "Cannot resolve keyword 'rating_alias' into field."
        with self.assertRaisesMessage(FieldError, msg):
            qs.distinct("rating_alias").first()