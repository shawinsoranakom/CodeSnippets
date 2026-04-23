def test_makemessages_no_settings(self):
        out, err = self.run_django_admin(["makemessages", "-l", "en", "-v", "0"])
        self.assertNoOutput(err)
        self.assertNoOutput(out)