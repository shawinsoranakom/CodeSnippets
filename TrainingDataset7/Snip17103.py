def test_duplicate_alias(self):
        # Regression for #11256 - duplicating a default alias raises
        # ValueError.
        msg = (
            "The named annotation 'authors__age__avg' conflicts with "
            "the default name for another annotation."
        )
        with self.assertRaisesMessage(ValueError, msg):
            Book.objects.annotate(
                Avg("authors__age"), authors__age__avg=Avg("authors__age")
            )