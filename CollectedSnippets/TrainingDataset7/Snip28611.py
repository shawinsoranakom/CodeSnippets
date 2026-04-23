def test_error_class(self):
        """
        Test the type of Formset and Form error attributes
        """
        Formset = modelformset_factory(User, fields="__all__")
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MAX_NUM_FORMS": "0",
            "form-0-id": "",
            "form-0-username": "apollo13",
            "form-0-serial": "1",
            "form-1-id": "",
            "form-1-username": "apollo13",
            "form-1-serial": "2",
        }
        formset = Formset(data)
        # check if the returned error classes are correct
        # note: formset.errors returns a list as documented
        self.assertIsInstance(formset.errors, list)
        self.assertIsInstance(formset.non_form_errors(), ErrorList)
        for form in formset.forms:
            self.assertIsInstance(form.errors, ErrorDict)
            self.assertIsInstance(form.non_field_errors(), ErrorList)