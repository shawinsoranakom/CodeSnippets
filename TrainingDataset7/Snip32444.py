def test_verbosity_1(self):
        stdout = StringIO()
        self.run_collectstatic(verbosity=1, stdout=stdout)
        output = stdout.getvalue()
        self.assertIn(self.staticfiles_copied_msg, output)
        self.assertNotIn(self.copying_msg, output)