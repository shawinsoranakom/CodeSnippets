def test_expressions(self):
        author = Author.objects.annotate(backward=Reverse(Trim("name"))).get(
            pk=self.john.pk
        )
        self.assertEqual(author.backward, self.john.name[::-1])
        with register_lookup(CharField, Reverse), register_lookup(CharField, Length):
            authors = Author.objects.all()
            self.assertCountEqual(
                authors.filter(name__reverse__length__gt=7), [self.john, self.elena]
            )
            self.assertCountEqual(
                authors.exclude(name__reverse__length__gt=7), [self.python]
            )