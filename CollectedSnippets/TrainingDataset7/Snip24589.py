def test16_annotated_date_queryset(self):
        """
        Ensure annotated date querysets work if spatial backend is used.  See
        #14648.
        """
        birth_years = [
            dt.year
            for dt in list(
                Author.objects.annotate(num_books=Count("books")).dates("dob", "year")
            )
        ]
        birth_years.sort()
        self.assertEqual([1950, 1974], birth_years)