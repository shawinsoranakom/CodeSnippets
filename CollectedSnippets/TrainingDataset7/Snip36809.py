def test_wrong_FK_value_raises_error(self):
        mtv = ModelToValidate(number=10, name="Some Name", parent_id=3)
        self.assertFieldFailsValidationWithMessage(
            mtv.full_clean,
            "parent",
            [
                "model to validate instance with id %r is not a valid choice."
                % mtv.parent_id
            ],
        )
        mtv = ModelToValidate(number=10, name="Some Name", ufm_id="Some Name")
        self.assertFieldFailsValidationWithMessage(
            mtv.full_clean,
            "ufm",
            [
                "unique fields model instance with unique_charfield %r is not "
                "a valid choice." % mtv.name
            ],
        )