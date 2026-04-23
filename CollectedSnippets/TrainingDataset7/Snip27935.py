def test_equal_notequal_hash(self):
        """
        Bug #9786: Ensure '==' and '!=' work correctly.
        Bug #9508: make sure hash() works as expected (equal items must
        hash to the same value).
        """
        # Create two Persons with different mugshots.
        p1 = self.PersonModel(name="Joe")
        p1.mugshot.save("mug", self.file1)
        p2 = self.PersonModel(name="Bob")
        p2.mugshot.save("mug", self.file2)
        self.assertIs(p1.mugshot == p2.mugshot, False)
        self.assertIs(p1.mugshot != p2.mugshot, True)

        # Test again with an instance fetched from the db.
        p1_db = self.PersonModel.objects.get(name="Joe")
        self.assertIs(p1_db.mugshot == p2.mugshot, False)
        self.assertIs(p1_db.mugshot != p2.mugshot, True)

        # Instance from db should match the local instance.
        self.assertIs(p1_db.mugshot == p1.mugshot, True)
        self.assertEqual(hash(p1_db.mugshot), hash(p1.mugshot))
        self.assertIs(p1_db.mugshot != p1.mugshot, False)