def test_import_loop(self):
        finders.get_finder.cache_clear()
        err = StringIO()
        msg = "Max post-process passes exceeded"
        with self.assertRaisesMessage(CommandError, msg) as cm:
            call_command("collectstatic", interactive=False, verbosity=0, stderr=err)
        self.assertIsInstance(cm.exception.__cause__, RuntimeError)
        self.assertEqual(
            "Post-processing 'bar.css, foo.css' failed!\n\n", err.getvalue()
        )
        self.assertPostCondition()