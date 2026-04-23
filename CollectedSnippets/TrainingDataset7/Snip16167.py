def test_available_apps(self):
        ctx = self.ctx
        apps = ctx["available_apps"]
        # we have registered two models from two different apps
        self.assertEqual(len(apps), 2)

        # admin_views.Article
        admin_views = apps[0]
        self.assertEqual(admin_views["app_label"], "admin_views")
        self.assertEqual(len(admin_views["models"]), 1)
        article = admin_views["models"][0]
        self.assertEqual(article["object_name"], "Article")
        self.assertEqual(article["model"], Article)

        # auth.User
        auth = apps[1]
        self.assertEqual(auth["app_label"], "auth")
        self.assertEqual(len(auth["models"]), 1)
        user = auth["models"][0]
        self.assertEqual(user["object_name"], "User")
        self.assertEqual(user["model"], User)

        self.assertEqual(auth["app_url"], "/test_admin/admin/auth/")
        self.assertIs(auth["has_module_perms"], True)

        self.assertIn("perms", user)
        self.assertIs(user["perms"]["add"], True)
        self.assertIs(user["perms"]["change"], True)
        self.assertIs(user["perms"]["delete"], True)
        self.assertEqual(user["admin_url"], "/test_admin/admin/auth/user/")
        self.assertEqual(user["add_url"], "/test_admin/admin/auth/user/add/")
        self.assertEqual(user["name"], "Users")