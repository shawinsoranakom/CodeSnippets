def test_verbosity_0(self):
        stdout = StringIO()
        self.run_collectstatic(verbosity=0, stdout=stdout)
        self.assertEqual(stdout.getvalue(), "")