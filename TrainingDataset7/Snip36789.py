def test_unique_fields_get_collected(self):
        m = UniqueFieldsModel()
        self.assertEqual(
            (
                [
                    (UniqueFieldsModel, ("id",)),
                    (UniqueFieldsModel, ("unique_charfield",)),
                    (UniqueFieldsModel, ("unique_integerfield",)),
                ],
                [],
            ),
            m._get_unique_checks(),
        )