def test_default_to_insertion_order(self):
        # Answers will always be ordered in the order they were inserted.
        self.assertQuerySetEqual(
            self.q1.answer_set.all(),
            [
                "John",
                "Paul",
                "George",
                "Ringo",
            ],
            attrgetter("text"),
        )