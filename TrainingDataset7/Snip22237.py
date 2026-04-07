def test_absolute_path(self):
        """
        Regression test for ticket #6436 --
        os.path.join will throw away the initial parts of a path if it
        encounters an absolute path.
        This means that if a fixture is specified as an absolute path,
        we need to make sure we don't discover the absolute path in every
        fixture directory.
        """
        load_absolute_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "absolute.json"
        )
        management.call_command(
            "loaddata",
            load_absolute_path,
            verbosity=0,
        )
        self.assertEqual(Absolute.objects.count(), 1)