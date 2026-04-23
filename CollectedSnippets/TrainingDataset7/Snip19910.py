def test_interactive_false(self):
        """non-interactive mode deletes stale content types."""
        with captured_stdout() as stdout:
            call_command("remove_stale_contenttypes", interactive=False, verbosity=2)
        self.assertIn("Deleting stale content type", stdout.getvalue())
        self.assertEqual(ContentType.objects.count(), self.before_count)