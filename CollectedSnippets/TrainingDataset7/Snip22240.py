def test_path_containing_dots(self):
        management.call_command(
            "loaddata",
            "path.containing.dots.json",
            verbosity=0,
        )
        self.assertEqual(Absolute.objects.count(), 1)