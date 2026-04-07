def test_without_for_user(self):
        msg = "Fourth argument to 'get_admin_log' must be 'for_user'"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            Template("{% load log %}{% get_admin_log 10 as admin_log foruser user %}")