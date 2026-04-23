def test_change_view(self):
        """Change view should restrict access and allow users to edit items."""
        change_dict = {
            "title": "Ikke fordømt",
            "content": "<p>edited article</p>",
            "date_0": "2008-03-18",
            "date_1": "10:54:39",
            "section": self.s1.pk,
        }
        article_change_url = reverse(
            "admin:admin_views_article_change", args=(self.a1.pk,)
        )
        article_changelist_url = reverse("admin:admin_views_article_changelist")

        # add user should not be able to view the list of article or change any
        # of them
        self.client.force_login(self.adduser)
        response = self.client.get(article_changelist_url)
        self.assertEqual(response.status_code, 403)
        response = self.client.get(article_change_url)
        self.assertEqual(response.status_code, 403)
        post = self.client.post(article_change_url, change_dict)
        self.assertEqual(post.status_code, 403)
        self.client.post(reverse("admin:logout"))

        # view user can view articles but not make changes.
        self.client.force_login(self.viewuser)
        response = self.client.get(article_changelist_url)
        self.assertContains(
            response,
            "<title>Select article to view | Django site admin</title>",
        )
        self.assertContains(response, "<h1>Select article to view</h1>")
        self.assertEqual(response.context["title"], "Select article to view")
        response = self.client.get(article_change_url)
        self.assertContains(
            response, "<title>- | View article | Django site admin</title>"
        )
        self.assertContains(response, "<h1>View article</h1>")
        self.assertContains(response, "<label>Extra form field:</label>")
        self.assertContains(
            response,
            '<a role="button" href="/test_admin/admin/admin_views/article/" '
            'class="closelink">Close</a>',
        )
        self.assertEqual(response.context["title"], "View article")
        post = self.client.post(article_change_url, change_dict)
        self.assertEqual(post.status_code, 403)
        self.assertEqual(
            Article.objects.get(pk=self.a1.pk).content, "<p>Middle content</p>"
        )
        self.client.post(reverse("admin:logout"))

        # change user can view all items and edit them
        self.client.force_login(self.changeuser)
        response = self.client.get(article_changelist_url)
        self.assertEqual(response.context["title"], "Select article to change")
        self.assertContains(
            response,
            "<title>Select article to change | Django site admin</title>",
        )
        self.assertContains(response, "<h1>Select article to change</h1>")
        response = self.client.get(article_change_url)
        self.assertEqual(response.context["title"], "Change article")
        self.assertContains(
            response,
            "<title>- | Change article | Django site admin</title>",
        )
        self.assertContains(response, "<h1>Change article</h1>")
        post = self.client.post(article_change_url, change_dict)
        self.assertRedirects(post, article_changelist_url)
        self.assertEqual(
            Article.objects.get(pk=self.a1.pk).content, "<p>edited article</p>"
        )

        # one error in form should produce singular error message, multiple
        # errors plural.
        change_dict["title"] = ""
        post = self.client.post(article_change_url, change_dict)
        self.assertContains(
            post,
            "Please correct the error below.",
            msg_prefix=(
                "Singular error message not found in response to post with one error"
            ),
        )

        change_dict["content"] = ""
        post = self.client.post(article_change_url, change_dict)
        self.assertContains(
            post,
            "Please correct the errors below.",
            msg_prefix=(
                "Plural error message not found in response to post with multiple "
                "errors"
            ),
        )
        self.client.post(reverse("admin:logout"))

        # Test redirection when using row-level change permissions. Refs
        # #11513.
        r1 = RowLevelChangePermissionModel.objects.create(id=1, name="odd id")
        r2 = RowLevelChangePermissionModel.objects.create(id=2, name="even id")
        r3 = RowLevelChangePermissionModel.objects.create(id=3, name="odd id mult 3")
        r6 = RowLevelChangePermissionModel.objects.create(id=6, name="even id mult 3")
        change_url_1 = reverse(
            "admin:admin_views_rowlevelchangepermissionmodel_change", args=(r1.pk,)
        )
        change_url_2 = reverse(
            "admin:admin_views_rowlevelchangepermissionmodel_change", args=(r2.pk,)
        )
        change_url_3 = reverse(
            "admin:admin_views_rowlevelchangepermissionmodel_change", args=(r3.pk,)
        )
        change_url_6 = reverse(
            "admin:admin_views_rowlevelchangepermissionmodel_change", args=(r6.pk,)
        )
        logins = [
            self.superuser,
            self.viewuser,
            self.adduser,
            self.changeuser,
            self.deleteuser,
        ]
        for login_user in logins:
            with self.subTest(login_user.username):
                self.client.force_login(login_user)
                response = self.client.get(change_url_1)
                self.assertEqual(response.status_code, 403)
                response = self.client.post(change_url_1, {"name": "changed"})
                self.assertEqual(
                    RowLevelChangePermissionModel.objects.get(id=1).name, "odd id"
                )
                self.assertEqual(response.status_code, 403)
                response = self.client.get(change_url_2)
                self.assertEqual(response.status_code, 200)
                response = self.client.post(change_url_2, {"name": "changed"})
                self.assertEqual(
                    RowLevelChangePermissionModel.objects.get(id=2).name, "changed"
                )
                self.assertRedirects(response, self.index_url)
                response = self.client.get(change_url_3)
                self.assertEqual(response.status_code, 200)
                response = self.client.post(change_url_3, {"name": "changed"})
                self.assertEqual(response.status_code, 403)
                self.assertEqual(
                    RowLevelChangePermissionModel.objects.get(id=3).name,
                    "odd id mult 3",
                )
                response = self.client.get(change_url_6)
                self.assertEqual(response.status_code, 200)
                response = self.client.post(change_url_6, {"name": "changed"})
                self.assertEqual(
                    RowLevelChangePermissionModel.objects.get(id=6).name, "changed"
                )
                self.assertRedirects(response, self.index_url)

                self.client.post(reverse("admin:logout"))

        for login_user in [self.joepublicuser, self.nostaffuser]:
            with self.subTest(login_user.username):
                self.client.force_login(login_user)
                response = self.client.get(change_url_1, follow=True)
                self.assertContains(response, "login-form")
                response = self.client.post(
                    change_url_1, {"name": "changed"}, follow=True
                )
                self.assertEqual(
                    RowLevelChangePermissionModel.objects.get(id=1).name, "odd id"
                )
                self.assertContains(response, "login-form")
                response = self.client.get(change_url_2, follow=True)
                self.assertContains(response, "login-form")
                response = self.client.post(
                    change_url_2, {"name": "changed again"}, follow=True
                )
                self.assertEqual(
                    RowLevelChangePermissionModel.objects.get(id=2).name, "changed"
                )
                self.assertContains(response, "login-form")
                self.client.post(reverse("admin:logout"))