def test_invalid_weights(self):
        invalid_weights = ["E", "Drandom", "AB", "C ", 0, "", " ", [1, 2, 3]]
        for weight in invalid_weights:
            with self.subTest(weight=weight):
                with self.assertRaisesMessage(
                    ValueError,
                    f"Weight must be one of 'A', 'B', 'C', and 'D', got {weight!r}.",
                ):
                    Line.objects.filter(
                        dialogue__search=Lexeme("kneecaps", weight=weight)
                    )