def test_content_type_rename_conflict(self):
        ContentType.objects.create(app_label="contenttypes_tests", model="foo")
        ContentType.objects.create(app_label="contenttypes_tests", model="renamedfoo")
        msg = (
            "Could not rename content type 'contenttypes_tests.foo' to "
            "'renamedfoo' due to an existing conflicting content type. "
            "Run 'remove_stale_contenttypes' to clean up stale entries."
        )
        with self.assertWarnsMessage(RuntimeWarning, msg):
            call_command(
                "migrate",
                "contenttypes_tests",
                database="default",
                interactive=False,
                verbosity=0,
            )
        self.assertTrue(
            ContentType.objects.filter(
                app_label="contenttypes_tests", model="foo"
            ).exists()
        )
        self.assertTrue(
            ContentType.objects.filter(
                app_label="contenttypes_tests", model="renamedfoo"
            ).exists()
        )
        msg = (
            "Could not rename content type 'contenttypes_tests.renamedfoo' to "
            "'foo' due to an existing conflicting content type. "
            "Run 'remove_stale_contenttypes' to clean up stale entries."
        )
        with self.assertWarnsMessage(RuntimeWarning, msg):
            call_command(
                "migrate",
                "contenttypes_tests",
                "zero",
                database="default",
                interactive=False,
                verbosity=0,
            )
        self.assertTrue(
            ContentType.objects.filter(
                app_label="contenttypes_tests", model="foo"
            ).exists()
        )
        self.assertTrue(
            ContentType.objects.filter(
                app_label="contenttypes_tests", model="renamedfoo"
            ).exists()
        )