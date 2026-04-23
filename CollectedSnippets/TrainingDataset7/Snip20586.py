def test_non_ascii(self):
        authors = Author.objects.annotate(first_initial=Left("name", 1))
        self.assertCountEqual(authors.filter(first_initial=Chr(ord("É"))), [self.elena])
        self.assertCountEqual(
            authors.exclude(first_initial=Chr(ord("É"))), [self.john, self.rhonda]
        )