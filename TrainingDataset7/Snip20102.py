def test_filter_first_name(self):
        self.assertSequenceEqual(
            Author.objects.filter(first_name__exact="John"),
            [self.a1],
        )