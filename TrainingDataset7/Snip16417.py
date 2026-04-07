def test_history_view(self):
        """History view should restrict access."""
        # add user should not be able to view the list of article or change any
        # of them
        self.client.force_login(self.adduser)
        response = self.client.get(
            reverse("admin:admin_views_article_history", args=(self.a1.pk,))
        )
        self.assertEqual(response.status_code, 403)
        self.client.post(reverse("admin:logout"))

        # view user can view all items
        self.client.force_login(self.viewuser)
        response = self.client.get(
            reverse("admin:admin_views_article_history", args=(self.a1.pk,))
        )
        self.assertEqual(response.status_code, 200)
        self.client.post(reverse("admin:logout"))

        # change user can view all items and edit them
        self.client.force_login(self.changeuser)
        response = self.client.get(
            reverse("admin:admin_views_article_history", args=(self.a1.pk,))
        )
        self.assertEqual(response.status_code, 200)

        # Test redirection when using row-level change permissions. Refs
        # #11513.
        rl1 = RowLevelChangePermissionModel.objects.create(id=1, name="odd id")
        rl2 = RowLevelChangePermissionModel.objects.create(id=2, name="even id")
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
                url = reverse(
                    "admin:admin_views_rowlevelchangepermissionmodel_history",
                    args=(rl1.pk,),
                )
                response = self.client.get(url)
                self.assertEqual(response.status_code, 403)

                url = reverse(
                    "admin:admin_views_rowlevelchangepermissionmodel_history",
                    args=(rl2.pk,),
                )
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

                self.client.post(reverse("admin:logout"))

        for login_user in [self.joepublicuser, self.nostaffuser]:
            with self.subTest(login_user.username):
                self.client.force_login(login_user)
                url = reverse(
                    "admin:admin_views_rowlevelchangepermissionmodel_history",
                    args=(rl1.pk,),
                )
                response = self.client.get(url, follow=True)
                self.assertContains(response, "login-form")
                url = reverse(
                    "admin:admin_views_rowlevelchangepermissionmodel_history",
                    args=(rl2.pk,),
                )
                response = self.client.get(url, follow=True)
                self.assertContains(response, "login-form")

                self.client.post(reverse("admin:logout"))