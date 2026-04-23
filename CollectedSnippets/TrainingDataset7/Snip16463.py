def test_generic_content_object_in_list_display(self):
        FunkyTag.objects.create(content_object=self.pl3, name="hott")
        response = self.client.get(reverse("admin:admin_views_funkytag_changelist"))
        self.assertContains(response, "%s</td>" % self.pl3)