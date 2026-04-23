def test_conditionally_show_change_section_link(self):
        """
        The foreign key widget should only show the "change related" button if
        the user has permission to change that related item.
        """

        def get_change_related(response):
            return (
                response.context["adminform"]
                .form.fields["section"]
                .widget.can_change_related
            )

        self.client.force_login(self.adduser)
        # The user can't change sections yet, so they shouldn't see the
        # "change section" link.
        url = reverse("admin:admin_views_article_add")
        change_link_text = "change_id_section"
        response = self.client.get(url)
        self.assertFalse(get_change_related(response))
        self.assertNotContains(response, change_link_text)
        # Allow the user to change sections too. Now they can see the
        # "change section" link.
        user = User.objects.get(username="adduser")
        perm = get_perm(Section, get_permission_codename("change", Section._meta))
        user.user_permissions.add(perm)
        response = self.client.get(url)
        self.assertTrue(get_change_related(response))
        self.assertContains(response, change_link_text)