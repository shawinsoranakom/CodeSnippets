def test_collectstatistic_no_post_process_replaced_paths(self):
        stdout = StringIO()
        self.run_collectstatic(verbosity=1, stdout=stdout)
        self.assertIn("post-processed", stdout.getvalue())