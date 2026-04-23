def test_tabular_inline_with_hidden_field_non_field_errors_has_correct_colspan(
        self,
    ):
        """
        In tabular inlines, when a form has non-field errors, those errors
        are rendered in a table line with a single cell spanning the whole
        table width. Colspan must be equal to the number of visible columns.
        """
        parent = SomeParentModel.objects.create(name="a")
        child = SomeChildModel.objects.create(name="b", position="0", parent=parent)
        url = reverse(
            "tabular_inline_hidden_field_admin:admin_inlines_someparentmodel_change",
            args=(parent.id,),
        )
        data = {
            "name": parent.name,
            "somechildmodel_set-TOTAL_FORMS": 1,
            "somechildmodel_set-INITIAL_FORMS": 1,
            "somechildmodel_set-MIN_NUM_FORMS": 0,
            "somechildmodel_set-MAX_NUM_FORMS": 1000,
            "_save": "Save",
            "somechildmodel_set-0-id": child.id,
            "somechildmodel_set-0-parent": parent.id,
            "somechildmodel_set-0-name": child.name,
            "somechildmodel_set-0-position": 1,
        }
        response = self.client.post(url, data)
        # Form has 3 visible columns and 1 hidden column.
        self.assertInHTML(
            '<thead><tr><th class="original"></th>'
            '<th class="column-name required">Name</th>'
            '<th class="column-position required hidden">Position'
            '<img src="/static/admin/img/icon-unknown.svg" '
            'class="help help-tooltip" width="10" height="10" '
            'alt="(Position help_text.)" '
            'title="Position help_text.">'
            "</th>"
            "<th>Delete?</th></tr></thead>",
            response.rendered_content,
        )
        # The non-field error must be spanned on 3 (visible) columns.
        self.assertInHTML(
            '<tr class="row-form-errors"><td colspan="3">'
            '<ul class="errorlist nonfield"><li>A non-field error</li></ul></td></tr>',
            response.rendered_content,
        )