def test_generic_update_or_create_when_updated(self):
        """
        Should be able to use update_or_create from the generic related manager
        to update a tag. Refs #23611.
        """
        count = self.bacon.tags.count()
        tag = self.bacon.tags.create(tag="stinky")
        self.assertEqual(count + 1, self.bacon.tags.count())
        tag, created = self.bacon.tags.update_or_create(
            defaults={"tag": "juicy"}, id=tag.id
        )
        self.assertFalse(created)
        self.assertEqual(count + 1, self.bacon.tags.count())
        self.assertEqual(tag.tag, "juicy")