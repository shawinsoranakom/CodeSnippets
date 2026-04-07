def test_generic_get_or_create_when_created(self):
        """
        Should be able to use get_or_create from the generic related manager
        to create a tag. Refs #23611.
        """
        count = self.bacon.tags.count()
        tag, created = self.bacon.tags.get_or_create(tag="stinky")
        self.assertTrue(created)
        self.assertEqual(count + 1, self.bacon.tags.count())