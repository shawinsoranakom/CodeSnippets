def test_limited_FK_raises_error(self):
        # The limit_choices_to on the parent field says that a parent object's
        # number attribute must be 10, so this should fail validation.
        parent = ModelToValidate.objects.create(number=11, name="Other Name")
        mtv = ModelToValidate(number=10, name="Some Name", parent_id=parent.pk)
        self.assertFailsValidation(mtv.full_clean, ["parent"])