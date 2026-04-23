def test_filtering(self):
        """
        Custom managers respond to usual filtering methods
        """
        self.assertQuerySetEqual(
            Book.published_objects.all(),
            [
                "How to program",
            ],
            lambda b: b.title,
        )