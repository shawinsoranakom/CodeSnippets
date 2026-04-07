def test_verbosity_1(self):
        for deletion_message, kwargs in [
            ("Deleting", {}),
            ("Pretending to delete", {"dry_run": True}),
        ]:
            with self.subTest(kwargs=kwargs):
                stdout = StringIO()
                self.run_collectstatic(verbosity=1, stdout=stdout, **kwargs)
                output = stdout.getvalue()
                self.assertIn("static file", output)
                self.assertIn("deleted", output)
                self.assertNotIn(deletion_message, output)