def test_null_argument(self):
        authors = Author.objects.annotate(
            nullif=NullIf("name", Value(None))
        ).values_list("nullif")
        self.assertCountEqual(authors, [("John Smith",), ("Rhonda",)])