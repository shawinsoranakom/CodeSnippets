def test_missing_arguments_raises_exception(self):
        with self.assertRaisesMessage(ValueError, "Both y and x must be provided."):
            StatAggregate(x=None, y=None)