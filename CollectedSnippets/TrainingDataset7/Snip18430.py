def test_view_user_password_is_readonly(self):
        u = User.objects.get(username="testclient")
        u.is_superuser = False
        u.save()
        original_password = u.password
        u.user_permissions.add(get_perm(User, "view_user"))
        response = self.client.get(
            reverse("auth_test_admin:auth_user_change", args=(u.pk,)),
        )
        algo, salt, hash_string = u.password.split("$")
        self.assertContains(response, '<div class="readonly">testclient</div>')
        # The password value is hashed.
        self.assertContains(
            response,
            "<strong>algorithm</strong>: <bdi>%s</bdi>\n\n"
            "<strong>salt</strong>: <bdi>%s********************</bdi>\n\n"
            "<strong>hash</strong>: <bdi>%s**************************</bdi>\n\n"
            % (
                algo,
                salt[:2],
                hash_string[:6],
            ),
            html=True,
        )
        self.assertNotContains(
            response,
            '<a role="button" class="button" href="../password/">Reset password</a>',
        )
        # Value in POST data is ignored.
        data = self.get_user_data(u)
        data["password"] = "shouldnotchange"
        change_url = reverse("auth_test_admin:auth_user_change", args=(u.pk,))
        response = self.client.post(change_url, data)
        self.assertEqual(response.status_code, 403)
        u.refresh_from_db()
        self.assertEqual(u.password, original_password)