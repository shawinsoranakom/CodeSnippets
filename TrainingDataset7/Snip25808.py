def test_values_list_filter_and_no_fields(self):
        # values_list() is similar to values(), except that the results are
        # returned as a list of tuples, rather than a list of dictionaries.
        # Within each tuple, the order of the elements is the same as the order
        # of fields in the values_list() call.
        self.assertSequenceEqual(
            Article.objects.filter(id__in=(self.a5.id, self.a6.id)).values_list(),
            [
                (
                    self.a5.id,
                    "Article 5",
                    datetime(2005, 8, 1, 9, 0),
                    self.au2.id,
                    "a5",
                ),
                (
                    self.a6.id,
                    "Article 6",
                    datetime(2005, 8, 1, 8, 0),
                    self.au2.id,
                    "a6",
                ),
            ],
        )