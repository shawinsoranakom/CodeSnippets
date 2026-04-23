def test_transform(self):
        with register_lookup(CharField, SHA512):
            authors = Author.objects.filter(
                alias__sha512=(
                    "ed014a19bb67a85f9c8b1d81e04a0e7101725be8627d79d02ca4f3bd8"
                    "03f33cf3b8fed53e80d2a12c0d0e426824d99d110f0919298a5055eff"
                    "f040a3fc091518"
                ),
            ).values_list("alias", flat=True)
            self.assertSequenceEqual(authors, ["John Smith"])