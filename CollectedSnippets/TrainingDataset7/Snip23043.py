def test_empty_forms_are_unbound(self):
        data = {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-0-title": "Test",
            "form-0-pub_date": "1904-06-16",
        }
        unbound_formset = ArticleFormSet()
        bound_formset = ArticleFormSet(data)
        empty_forms = [unbound_formset.empty_form, bound_formset.empty_form]
        # Empty forms should be unbound
        self.assertFalse(empty_forms[0].is_bound)
        self.assertFalse(empty_forms[1].is_bound)
        # The empty forms should be equal.
        self.assertHTMLEqual(empty_forms[0].as_p(), empty_forms[1].as_p())