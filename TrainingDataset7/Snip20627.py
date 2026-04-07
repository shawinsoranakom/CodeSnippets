def test_transform(self):
        with register_lookup(CharField, Reverse):
            authors = Author.objects.all()
            self.assertCountEqual(
                authors.filter(name__reverse=self.john.name[::-1]), [self.john]
            )
            self.assertCountEqual(
                authors.exclude(name__reverse=self.john.name[::-1]),
                [self.elena, self.python],
            )