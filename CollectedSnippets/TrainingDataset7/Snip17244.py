def test_update_with_alias(self):
        Book.objects.alias(
            other_rating=F("rating") - 1,
        ).update(rating=F("other_rating"))
        self.b1.refresh_from_db()
        self.assertEqual(self.b1.rating, 3.5)