def test_conditionally_show_add_section_link(self):
        """
        The foreign key widget should only show the "add related" button if the
        user has permission to add that related item.
        """
        self.client.force_login(self.adduser)
        # The user can't add sections yet, so they shouldn't see the "add
        # section" link.
        url = reverse("admin:admin_views_article_add")
        add_link_text = "add_id_section"
        response = self.client.get(url)
        self.assertNotContains(response, add_link_text)
        # Allow the user to add sections too. Now they can see the "add
        # section" link.
        user = User.objects.get(username="adduser")
        perm = get_perm(Section, get_permission_codename("add", Section._meta))
        user.user_permissions.add(perm)
        response = self.client.get(url)
        self.assertContains(response, add_link_text)