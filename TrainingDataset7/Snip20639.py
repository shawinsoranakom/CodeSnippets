def test_transform(self):
        with register_lookup(CharField, SHA224):
            authors = Author.objects.filter(
                alias__sha224=(
                    "a61303c220731168452cb6acf3759438b1523e768f464e3704e12f70"
                ),
            ).values_list("alias", flat=True)
            self.assertSequenceEqual(authors, ["John Smith"])