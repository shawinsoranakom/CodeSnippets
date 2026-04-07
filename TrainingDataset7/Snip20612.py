def test_transform(self):
        with register_lookup(CharField, Ord):
            authors = Author.objects.annotate(first_initial=Left("name", 1))
            self.assertCountEqual(
                authors.filter(first_initial__ord=ord("J")), [self.john]
            )
            self.assertCountEqual(
                authors.exclude(first_initial__ord=ord("J")), [self.elena, self.rhonda]
            )