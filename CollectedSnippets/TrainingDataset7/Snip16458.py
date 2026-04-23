def test_generic_relations(self):
        """
        If a deleted object has GenericForeignKeys pointing to it,
        those objects should be listed for deletion.
        """
        plot = self.pl3
        tag = FunkyTag.objects.create(content_object=plot, name="hott")
        should_contain = '<li>Funky tag: <a href="%s">hott' % reverse(
            "admin:admin_views_funkytag_change", args=(tag.id,)
        )
        response = self.client.get(
            reverse("admin:admin_views_plot_delete", args=(plot.pk,))
        )
        self.assertContains(response, should_contain)