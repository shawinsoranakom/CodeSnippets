def test_post_processing_nonutf8(self):
        finders.get_finder.cache_clear()
        err = StringIO()
        with self.assertRaises(CommandError) as cm:
            call_command("collectstatic", interactive=False, verbosity=0, stderr=err)
        self.assertIsInstance(cm.exception.__cause__, UnicodeDecodeError)
        self.assertEqual("Post-processing 'nonutf8.css' failed!\n\n", err.getvalue())
        self.assertPostCondition()