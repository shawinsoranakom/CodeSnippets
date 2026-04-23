def test_concrete_abstract_concrete_pk(self):
        """
        Primary key set correctly with concrete->abstract->concrete
        inheritance.
        """
        # Regression test for #13987: Primary key is incorrectly determined
        # when more than one model has a concrete->abstract->concrete
        # inheritance hierarchy.
        self.assertEqual(
            len(
                [field for field in BusStation._meta.local_fields if field.primary_key]
            ),
            1,
        )
        self.assertEqual(
            len(
                [
                    field
                    for field in TrainStation._meta.local_fields
                    if field.primary_key
                ]
            ),
            1,
        )
        self.assertIs(BusStation._meta.pk.model, BusStation)
        self.assertIs(TrainStation._meta.pk.model, TrainStation)