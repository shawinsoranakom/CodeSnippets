def test_second_call_doesnt_crash(self):
        out = io.StringIO()
        management.call_command("createcachetable", stdout=out)
        self.assertEqual(
            out.getvalue(),
            "Cache table 'test cache table' already exists.\n" * len(settings.CACHES),
        )