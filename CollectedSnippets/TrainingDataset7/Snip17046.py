def test_string_agg_filter(self):
        values = Book.objects.aggregate(
            stringagg=StringAgg(
                "name",
                delimiter=Value(";"),
                filter=Q(name__startswith="P"),
            )
        )

        expected_values = {
            "stringagg": "Practical Django Projects;"
            "Python Web Development with Django;Paradigms of Artificial "
            "Intelligence Programming: Case Studies in Common Lisp",
        }
        self.assertEqual(values, expected_values)