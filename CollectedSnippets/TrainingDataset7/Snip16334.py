def test_changelist_with_no_change_url(self):
        """
        ModelAdmin.changelist_view shouldn't result in a NoReverseMatch if url
        for change_view is removed from get_urls (#20934).
        """
        o = UnchangeableObject.objects.create()
        response = self.client.get(
            reverse("admin:admin_views_unchangeableobject_changelist")
        )
        # Check the format of the shown object -- shouldn't contain a change
        # link
        self.assertContains(
            response, '<th class="field-__str__">%s</th>' % o, html=True
        )