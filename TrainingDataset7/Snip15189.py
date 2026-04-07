def test_non_integer_limit(self):
        msg = "First argument to 'get_admin_log' must be an integer"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            Template(
                '{% load log %}{% get_admin_log "10" as admin_log for_user user %}'
            )