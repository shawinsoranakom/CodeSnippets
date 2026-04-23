def test_post_processing_failure(self):
        """
        post_processing indicates the origin of the error when it fails.
        """
        finders.get_finder.cache_clear()
        err = StringIO()
        with self.assertRaises(CommandError) as cm:
            call_command("collectstatic", interactive=False, verbosity=0, stderr=err)
        self.assertEqual("Post-processing 'faulty.css' failed!\n\n", err.getvalue())
        self.assertIsInstance(cm.exception.__cause__, ValueError)
        exc_message = str(cm.exception)
        self.assertIn("faulty.css", exc_message)
        self.assertIn("missing.css", exc_message)
        self.assertIn("1:", exc_message)  # line 1 reported
        self.assertPostCondition()