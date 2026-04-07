def test_interactive_true_without_dependent_objects(self):
        """
        interactive mode deletes stale content types even if there aren't any
        dependent objects.
        """
        with mock.patch("builtins.input", return_value="yes"):
            with captured_stdout() as stdout:
                call_command("remove_stale_contenttypes", verbosity=2)
        self.assertIn("Deleting stale content type", stdout.getvalue())
        self.assertEqual(ContentType.objects.count(), self.before_count)