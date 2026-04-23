def test_loaddata_works_when_fixture_has_forward_refs(self):
        """
        Forward references cause fixtures not to load in MySQL (InnoDB).
        """
        management.call_command(
            "loaddata",
            "forward_ref.json",
            verbosity=0,
        )
        self.assertEqual(Book.objects.all()[0].id, 1)
        self.assertEqual(Person.objects.all()[0].id, 4)