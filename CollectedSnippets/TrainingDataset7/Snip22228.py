def test_duplicate_pk(self):
        """
        This is a regression test for ticket #3790.
        """
        # Load a fixture that uses PK=1
        management.call_command(
            "loaddata",
            "sequence",
            verbosity=0,
        )

        # Create a new animal. Without a sequence reset, this new object
        # will take a PK of 1 (on Postgres), and the save will fail.

        animal = Animal(
            name="Platypus",
            latin_name="Ornithorhynchus anatinus",
            count=2,
            weight=2.2,
        )
        animal.save()
        self.assertGreater(animal.id, 1)