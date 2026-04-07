def test_change_list_null_boolean_display(self):
        Post.objects.create(public=None)
        response = self.client.get(reverse("admin:admin_views_post_changelist"))
        self.assertContains(response, "icon-unknown.svg")