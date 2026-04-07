def test_setattr_raises_validation_error_field_specific(self):
        """
        A model ValidationError using the dict form should put the error
        message into the correct key of form.errors.
        """
        form_class = modelform_factory(
            model=StrictAssignmentFieldSpecific, fields=["title"]
        )
        form = form_class(data={"title": "testing setattr"}, files=None)
        # This line turns on the ValidationError; it avoids the model erroring
        # when its own __init__() is called when creating form.instance.
        form.instance._should_error = True
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {"title": ["Cannot set attribute", "This field cannot be blank."]},
        )