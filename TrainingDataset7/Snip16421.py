def test_conditionally_show_delete_section_link(self):
        """
        The foreign key widget should only show the "delete related" button if
        the user has permission to delete that related item.
        """

        def get_delete_related(response):
            return (
                response.context["adminform"]
                .form.fields["sub_section"]
                .widget.can_delete_related
            )

        self.client.force_login(self.adduser)
        # The user can't delete sections yet, so they shouldn't see the
        # "delete section" link.
        url = reverse("admin:admin_views_article_add")
        delete_link_text = "delete_id_sub_section"
        response = self.client.get(url)
        self.assertFalse(get_delete_related(response))
        self.assertNotContains(response, delete_link_text)
        # Allow the user to delete sections too. Now they can see the
        # "delete section" link.
        user = User.objects.get(username="adduser")
        perm = get_perm(Section, get_permission_codename("delete", Section._meta))
        user.user_permissions.add(perm)
        response = self.client.get(url)
        self.assertTrue(get_delete_related(response))
        self.assertContains(response, delete_link_text)