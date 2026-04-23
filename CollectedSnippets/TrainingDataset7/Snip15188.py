def test_missing_args(self):
        msg = "'get_admin_log' statements require two arguments"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            Template("{% load log %}{% get_admin_log 10 as %}")