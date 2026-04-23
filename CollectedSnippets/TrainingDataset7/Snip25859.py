def test_isnull_textfield(self):
        self.assertSequenceEqual(
            Author.objects.filter(bio__isnull=True),
            [self.au2],
        )
        self.assertSequenceEqual(
            Author.objects.filter(bio__isnull=False),
            [self.au1],
        )