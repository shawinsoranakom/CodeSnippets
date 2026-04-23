def test_unique_together_gets_picked_up_and_converted_to_tuple(self):
        m = UniqueTogetherModel()
        self.assertEqual(
            (
                [
                    (UniqueTogetherModel, ("ifield", "cfield")),
                    (UniqueTogetherModel, ("ifield", "efield")),
                    (UniqueTogetherModel, ("id",)),
                ],
                [],
            ),
            m._get_unique_checks(),
        )