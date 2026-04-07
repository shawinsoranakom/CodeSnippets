def test_basic(self):
        authors = Author.objects.annotate(first_initial=Left("name", 1))
        self.assertCountEqual(authors.filter(first_initial=Chr(ord("J"))), [self.john])
        self.assertCountEqual(
            authors.exclude(first_initial=Chr(ord("J"))), [self.elena, self.rhonda]
        )