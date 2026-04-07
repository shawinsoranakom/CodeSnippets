def test_form_errors_are_caught_by_formset(self):
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-0-title": "Test",
            "form-0-pub_date": "1904-06-16",
            "form-1-title": "Test",
            "form-1-pub_date": "",  # <-- this date is missing but required
        }
        formset = ArticleFormSet(data)
        self.assertFalse(formset.is_valid())
        self.assertEqual(
            [{}, {"pub_date": ["This field is required."]}], formset.errors
        )