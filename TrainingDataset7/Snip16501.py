def test_pk_hidden_fields(self):
        """
        hidden pk fields aren't displayed in the table body and their
        corresponding human-readable value is displayed instead. The hidden pk
        fields are displayed but separately (not in the table) and only once.
        """
        story1 = Story.objects.create(
            title="The adventures of Guido", content="Once upon a time in Djangoland..."
        )
        story2 = Story.objects.create(
            title="Crouching Tiger, Hidden Python",
            content="The Python was sneaking into...",
        )
        response = self.client.get(reverse("admin:admin_views_story_changelist"))
        # Only one hidden field, in a separate place than the table.
        self.assertContains(response, 'id="id_form-0-id"', 1)
        self.assertContains(response, 'id="id_form-1-id"', 1)
        self.assertContains(
            response,
            '<div class="hiddenfields">\n'
            '<input type="hidden" name="form-0-id" value="%s" id="id_form-0-id">'
            '<input type="hidden" name="form-1-id" value="%s" id="id_form-1-id">\n'
            "</div>" % (story2.id, story1.id),
            html=True,
        )
        self.assertContains(response, '<td class="field-id">%s</td>' % story1.id, 1)
        self.assertContains(response, '<td class="field-id">%s</td>' % story2.id, 1)