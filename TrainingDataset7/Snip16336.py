def test_resolve_admin_views(self):
        index_match = resolve("/test_admin/admin4/")
        list_match = resolve("/test_admin/admin4/auth/user/")
        self.assertIs(index_match.func.admin_site, customadmin.simple_site)
        self.assertIsInstance(
            list_match.func.model_admin, customadmin.CustomPwdTemplateUserAdmin
        )