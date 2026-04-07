def test_view_subtitle_per_object(self):
        viewuser = User.objects.create_user(
            username="viewuser",
            password="secret",
            is_staff=True,
        )
        viewuser.user_permissions.add(
            get_perm(Article, get_permission_codename("view", Article._meta)),
        )
        self.client.force_login(viewuser)
        response = self.client.get(
            reverse("admin:admin_views_article_change", args=(self.a1.pk,)),
        )
        self.assertContains(
            response,
            "<title>Article 1 | View article | Django site admin</title>",
        )
        self.assertContains(response, "<h1>View article</h1>")
        self.assertContains(response, "<h2>Article 1</h2>")
        response = self.client.get(
            reverse("admin:admin_views_article_change", args=(self.a2.pk,)),
        )
        self.assertContains(
            response,
            "<title>Article 2 | View article | Django site admin</title>",
        )
        self.assertContains(response, "<h1>View article</h1>")
        self.assertContains(response, "<h2>Article 2</h2>")