def test_changelist_field_classes(self):
        """
        Cells of the change list table should contain the field name in their
        class attribute.
        """
        Podcast.objects.create(name="Django Dose", release_date=datetime.date.today())
        response = self.client.get(reverse("admin:admin_views_podcast_changelist"))
        self.assertContains(response, '<th class="field-name">')
        self.assertContains(response, '<td class="field-release_date nowrap">')
        self.assertContains(response, '<td class="action-checkbox">')