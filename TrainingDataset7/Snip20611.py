def test_basic(self):
        authors = Author.objects.annotate(name_part=Ord("name"))
        self.assertCountEqual(
            authors.filter(name_part__gt=Ord(Value("John"))), [self.elena, self.rhonda]
        )
        self.assertCountEqual(
            authors.exclude(name_part__gt=Ord(Value("John"))), [self.john]
        )