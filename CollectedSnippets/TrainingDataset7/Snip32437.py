def test_collectstatis_check(self):
        msg = "The STATICFILES_DIRS setting is not a tuple or list."
        with self.assertRaisesMessage(SystemCheckError, msg):
            call_command("collectstatic", skip_checks=False)