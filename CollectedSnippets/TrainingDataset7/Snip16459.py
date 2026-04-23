def test_generic_relations_with_related_query_name(self):
        """
        If a deleted object has GenericForeignKey with
        GenericRelation(related_query_name='...') pointing to it, those objects
        should be listed for deletion.
        """
        bookmark = Bookmark.objects.create(name="djangoproject")
        tag = FunkyTag.objects.create(content_object=bookmark, name="django")
        tag_url = reverse("admin:admin_views_funkytag_change", args=(tag.id,))
        should_contain = '<li>Funky tag: <a href="%s">django' % tag_url
        response = self.client.get(
            reverse("admin:admin_views_bookmark_delete", args=(bookmark.pk,))
        )
        self.assertContains(response, should_contain)