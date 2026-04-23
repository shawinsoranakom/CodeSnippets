def test_loaddata_with_valid_fixture_dirs(self):
        management.call_command(
            "loaddata",
            "absolute.json",
            verbosity=0,
        )