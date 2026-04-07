def test_transform(self):
        with register_lookup(CharField, MD5):
            authors = Author.objects.filter(
                alias__md5="6117323d2cabbc17d44c2b44587f682c",
            ).values_list("alias", flat=True)
            self.assertSequenceEqual(authors, ["John Smith"])