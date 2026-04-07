def test_tabular_non_field_errors(self):
        """
        non_field_errors are displayed correctly, including the correct value
        for colspan.
        """
        data = {
            "title_set-TOTAL_FORMS": 1,
            "title_set-INITIAL_FORMS": 0,
            "title_set-MAX_NUM_FORMS": 0,
            "_save": "Save",
            "title_set-0-title1": "a title",
            "title_set-0-title2": "a different title",
        }
        response = self.client.post(
            reverse("admin:admin_inlines_titlecollection_add"), data
        )
        # Here colspan is "4": two fields (title1 and title2), one hidden field
        # and the delete checkbox.
        self.assertContains(
            response,
            '<tr class="row-form-errors"><td colspan="4">'
            '<ul class="errorlist nonfield">'
            "<li>The two titles must be the same</li></ul></td></tr>",
        )