def test_transform(self):
        with register_lookup(CharField, SHA1):
            authors = Author.objects.filter(
                alias__sha1="e61a3587b3f7a142b8c7b9263c82f8119398ecb7",
            ).values_list("alias", flat=True)
            self.assertSequenceEqual(authors, ["John Smith"])