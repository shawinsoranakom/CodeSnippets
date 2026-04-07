def test_contenttypes_removed_in_installed_apps_without_models(self):
        ContentType.objects.create(app_label="empty_models", model="Fake 1")
        ContentType.objects.create(app_label="no_models", model="Fake 2")
        with (
            mock.patch("builtins.input", return_value="yes"),
            captured_stdout() as stdout,
        ):
            call_command("remove_stale_contenttypes", verbosity=2)
        self.assertNotIn(
            "Deleting stale content type 'empty_models | Fake 1'",
            stdout.getvalue(),
        )
        self.assertIn(
            "Deleting stale content type 'no_models | Fake 2'",
            stdout.getvalue(),
        )
        self.assertEqual(ContentType.objects.count(), self.before_count + 1)