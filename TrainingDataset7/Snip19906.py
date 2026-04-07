def setUpTestData(cls):
        with captured_stdout():
            call_command(
                "remove_stale_contenttypes",
                interactive=False,
                include_stale_apps=True,
                verbosity=2,
            )
        cls.before_count = ContentType.objects.count()
        cls.content_type = ContentType.objects.create(
            app_label="contenttypes_tests", model="Fake"
        )