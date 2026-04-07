def test_transform(self):
        with register_lookup(CharField, SHA256):
            authors = Author.objects.filter(
                alias__sha256=(
                    "ef61a579c907bbed674c0dbcbcf7f7af8f851538eef7b8e58c5bee0b8cfdac4a"
                ),
            ).values_list("alias", flat=True)
            self.assertSequenceEqual(authors, ["John Smith"])