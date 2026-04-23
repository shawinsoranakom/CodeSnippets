def test_transform(self):
        with register_lookup(CharField, SHA384):
            authors = Author.objects.filter(
                alias__sha384=(
                    "9df976bfbcf96c66fbe5cba866cd4deaa8248806f15b69c4010a404112906e4ca7"
                    "b57e53b9967b80d77d4f5c2982cbc8"
                ),
            ).values_list("alias", flat=True)
            self.assertSequenceEqual(authors, ["John Smith"])