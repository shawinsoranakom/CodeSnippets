def test_inline_hidden_field_no_column(self):
        """
        #18263 -- Make sure hidden fields don't get a column in tabular inlines
        """
        parent = SomeParentModel.objects.create(name="a")
        SomeChildModel.objects.create(name="b", position="0", parent=parent)
        SomeChildModel.objects.create(name="c", position="1", parent=parent)
        response = self.client.get(
            reverse("admin:admin_inlines_someparentmodel_change", args=(parent.pk,))
        )
        self.assertNotContains(response, '<td class="field-position">')
        self.assertInHTML(
            '<input id="id_somechildmodel_set-1-position" '
            'name="somechildmodel_set-1-position" type="hidden" value="1">',
            response.rendered_content,
        )