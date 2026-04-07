def test_invalid_keyword_argument(self):
        """
        View arguments must be predefined on the class and can't
        be named like an HTTP method.
        """
        msg = (
            "The method name %s is not accepted as a keyword argument to "
            "SimpleView()."
        )
        # Check each of the allowed method names
        for method in SimpleView.http_method_names:
            with self.assertRaisesMessage(TypeError, msg % method):
                SimpleView.as_view(**{method: "value"})

        # Check the case view argument is ok if predefined on the class...
        CustomizableView.as_view(parameter="value")
        # ...but raises errors otherwise.
        msg = (
            "CustomizableView() received an invalid keyword 'foobar'. "
            "as_view only accepts arguments that are already attributes of "
            "the class."
        )
        with self.assertRaisesMessage(TypeError, msg):
            CustomizableView.as_view(foobar="value")