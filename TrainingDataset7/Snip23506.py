def test_generic_get_or_create_when_exists(self):
        """
        Should be able to use get_or_create from the generic related manager
        to get a tag. Refs #23611.
        """
        count = self.bacon.tags.count()
        tag = self.bacon.tags.create(tag="stinky")
        self.assertEqual(count + 1, self.bacon.tags.count())
        tag, created = self.bacon.tags.get_or_create(
            id=tag.id, defaults={"tag": "juicy"}
        )
        self.assertFalse(created)
        self.assertEqual(count + 1, self.bacon.tags.count())
        # shouldn't had changed the tag
        self.assertEqual(tag.tag, "stinky")