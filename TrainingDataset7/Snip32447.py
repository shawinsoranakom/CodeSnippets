def test_verbosity_2_with_post_process(self):
        stdout = StringIO()
        self.run_collectstatic(verbosity=2, stdout=stdout, post_process=True)
        self.assertIn(self.post_process_msg, stdout.getvalue())