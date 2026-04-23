def test_verbosity_2(self):
        stdout = StringIO()
        self.run_collectstatic(verbosity=2, stdout=stdout)
        output = stdout.getvalue()
        self.assertIn(self.staticfiles_copied_msg, output)
        self.assertIn(self.copying_msg, output)