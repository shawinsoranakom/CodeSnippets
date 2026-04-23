def test_setattr_raises_validation_error_non_field(self):
        """
        A model ValidationError not using the dict form should put the error
        message into __all__ (i.e. non-field errors) on the form.
        """
        form_class = modelform_factory(model=StrictAssignmentAll, fields=["title"])
        form = form_class(data={"title": "testing setattr"}, files=None)
        # This line turns on the ValidationError; it avoids the model erroring
        # when its own __init__() is called when creating form.instance.
        form.instance._should_error = True
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors,
            {
                "__all__": ["Cannot set attribute"],
                "title": ["This field cannot be blank."],
            },
        )