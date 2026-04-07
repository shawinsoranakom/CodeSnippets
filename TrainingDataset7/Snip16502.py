def test_pk_hidden_fields_with_list_display_links(self):
        """Similarly as test_pk_hidden_fields, but when the hidden pk fields
        are referenced in list_display_links. Refs #12475.
        """
        story1 = OtherStory.objects.create(
            title="The adventures of Guido",
            content="Once upon a time in Djangoland...",
        )
        story2 = OtherStory.objects.create(
            title="Crouching Tiger, Hidden Python",
            content="The Python was sneaking into...",
        )
        link1 = reverse("admin:admin_views_otherstory_change", args=(story1.pk,))
        link2 = reverse("admin:admin_views_otherstory_change", args=(story2.pk,))
        response = self.client.get(reverse("admin:admin_views_otherstory_changelist"))
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
        self.assertContains(
            response,
            '<th class="field-id"><a href="%s">%s</a></th>' % (link1, story1.id),
            1,
        )
        self.assertContains(
            response,
            '<th class="field-id"><a href="%s">%s</a></th>' % (link2, story2.id),
            1,
        )