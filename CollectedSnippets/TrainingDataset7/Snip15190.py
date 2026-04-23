def test_without_as(self):
        msg = "Second argument to 'get_admin_log' must be 'as'"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            Template("{% load log %}{% get_admin_log 10 ad admin_log for_user user %}")