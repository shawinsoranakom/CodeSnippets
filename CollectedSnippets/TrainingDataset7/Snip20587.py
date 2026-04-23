def test_transform(self):
        with register_lookup(IntegerField, Chr):
            authors = Author.objects.annotate(name_code_point=Ord("name"))
            self.assertCountEqual(
                authors.filter(name_code_point__chr=Chr(ord("J"))), [self.john]
            )
            self.assertCountEqual(
                authors.exclude(name_code_point__chr=Chr(ord("J"))),
                [self.elena, self.rhonda],
            )