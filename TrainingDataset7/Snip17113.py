def test_annotate_and_count(self):
        # Regression for 10425 - annotations don't get in the way of a count()
        # clause
        self.assertEqual(
            Book.objects.values("publisher").annotate(Count("publisher")).count(), 4
        )
        self.assertEqual(
            Book.objects.annotate(Count("publisher")).values("publisher").count(), 6
        )