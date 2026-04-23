def test_slicing_can_slice_again_after_slicing(self):
        self.assertSequenceEqual(
            self.get_ordered_articles()[0:5][0:2],
            [self.articles[0], self.articles[1]],
        )
        self.assertSequenceEqual(
            self.get_ordered_articles()[0:5][4:], [self.articles[4]]
        )
        self.assertSequenceEqual(self.get_ordered_articles()[0:5][5:], [])

        # Some more tests!
        self.assertSequenceEqual(
            self.get_ordered_articles()[2:][0:2],
            [self.articles[2], self.articles[3]],
        )
        self.assertSequenceEqual(
            self.get_ordered_articles()[2:][:2],
            [self.articles[2], self.articles[3]],
        )
        self.assertSequenceEqual(
            self.get_ordered_articles()[2:][2:3], [self.articles[4]]
        )

        # Using an offset without a limit is also possible.
        self.assertSequenceEqual(
            self.get_ordered_articles()[5:],
            [self.articles[5], self.articles[6]],
        )