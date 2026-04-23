def test_verbosity_1_with_post_process(self):
        stdout = StringIO()
        self.run_collectstatic(verbosity=1, stdout=stdout, post_process=True)
        self.assertNotIn(self.post_process_msg, stdout.getvalue())