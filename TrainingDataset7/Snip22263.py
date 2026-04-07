def test_fixtures_dir_pathlib(self):
        management.call_command("loaddata", "inner/absolute.json", verbosity=0)
        self.assertQuerySetEqual(Absolute.objects.all(), [1], transform=lambda o: o.pk)