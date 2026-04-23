def test_loaddata_forward_refs_split_fixtures(self):
        """
        Regression for #17530 - should be able to cope with forward references
        when the fixtures are not in the same files or directories.
        """
        management.call_command(
            "loaddata",
            "forward_ref_1.json",
            "forward_ref_2.json",
            verbosity=0,
        )
        self.assertEqual(Book.objects.all()[0].id, 1)
        self.assertEqual(Person.objects.all()[0].id, 4)