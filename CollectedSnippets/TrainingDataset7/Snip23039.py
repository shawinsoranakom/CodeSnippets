def test_management_form_invalid_data(self):
        data = {
            "form-TOTAL_FORMS": "two",
            "form-INITIAL_FORMS": "one",
        }
        formset = ArticleFormSet(data)
        self.assertIs(formset.is_valid(), False)
        self.assertEqual(
            formset.non_form_errors(),
            [
                "ManagementForm data is missing or has been tampered with. "
                "Missing fields: form-TOTAL_FORMS, form-INITIAL_FORMS. "
                "You may need to file a bug report if the issue persists.",
            ],
        )
        self.assertEqual(formset.errors, [])
        # Can still render the formset.
        self.assertHTMLEqual(
            str(formset),
            '<ul class="errorlist nonfield">'
            "<li>(Hidden field TOTAL_FORMS) Enter a whole number.</li>"
            "<li>(Hidden field INITIAL_FORMS) Enter a whole number.</li>"
            "</ul>"
            "<div>"
            '<input type="hidden" name="form-TOTAL_FORMS" value="two" '
            'id="id_form-TOTAL_FORMS">'
            '<input type="hidden" name="form-INITIAL_FORMS" value="one" '
            'id="id_form-INITIAL_FORMS">'
            '<input type="hidden" name="form-MIN_NUM_FORMS" id="id_form-MIN_NUM_FORMS">'
            '<input type="hidden" name="form-MAX_NUM_FORMS" id="id_form-MAX_NUM_FORMS">'
            "</div>\n",
        )