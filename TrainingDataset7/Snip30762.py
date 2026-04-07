def test_slicing_with_steps_can_be_used(self):
        self.assertSequenceEqual(
            self.get_ordered_articles()[::2],
            [
                self.articles[0],
                self.articles[2],
                self.articles[4],
                self.articles[6],
            ],
        )