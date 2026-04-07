def test_non_nullable_fk_not_promoted(self):
        qs = Book.objects.annotate(Count("contact__name"))
        self.assertIn(" INNER JOIN ", str(qs.query))