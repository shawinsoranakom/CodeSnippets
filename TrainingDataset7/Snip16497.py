def test_list_editable_pagination(self):
        """
        Pagination works for list_editable items.
        """
        UnorderedObject.objects.create(id=1, name="Unordered object #1")
        UnorderedObject.objects.create(id=2, name="Unordered object #2")
        UnorderedObject.objects.create(id=3, name="Unordered object #3")
        response = self.client.get(
            reverse("admin:admin_views_unorderedobject_changelist")
        )
        self.assertContains(response, "Unordered object #3")
        self.assertContains(response, "Unordered object #2")
        self.assertNotContains(response, "Unordered object #1")
        response = self.client.get(
            reverse("admin:admin_views_unorderedobject_changelist") + "?p=2"
        )
        self.assertNotContains(response, "Unordered object #3")
        self.assertNotContains(response, "Unordered object #2")
        self.assertContains(response, "Unordered object #1")