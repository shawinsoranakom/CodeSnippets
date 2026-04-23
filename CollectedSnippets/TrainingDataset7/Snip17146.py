def test_annotate_reserved_word(self):
        """
        Regression #18333 - Ensure annotated column name is properly quoted.
        """
        vals = Book.objects.annotate(select=Count("authors__id")).aggregate(
            Sum("select"), Avg("select")
        )
        self.assertEqual(
            vals,
            {
                "select__sum": 10,
                "select__avg": Approximate(1.666, places=2),
            },
        )