def test_author_filtering(self):
        self.assertSequenceEqual(
            Author.objects.filter(first_name__exact="John"),
            [self.a1],
        )