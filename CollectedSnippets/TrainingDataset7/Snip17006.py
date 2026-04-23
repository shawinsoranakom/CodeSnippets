def test_aggregation_exists_multivalued_outeref(self):
        self.assertCountEqual(
            Publisher.objects.annotate(
                books_exists=Exists(
                    Book.objects.filter(publisher=OuterRef("book__publisher"))
                ),
                books_count=Count("book"),
            ),
            Publisher.objects.all(),
        )