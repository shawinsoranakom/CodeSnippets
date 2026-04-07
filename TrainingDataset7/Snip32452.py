def test_verbosity_0(self):
        for kwargs in [{}, {"dry_run": True}]:
            with self.subTest(kwargs=kwargs):
                stdout = StringIO()
                self.run_collectstatic(verbosity=0, stdout=stdout, **kwargs)
                self.assertEqual(stdout.getvalue(), "")