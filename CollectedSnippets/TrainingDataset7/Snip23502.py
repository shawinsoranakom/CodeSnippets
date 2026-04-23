def test_generic_update_or_create_when_updated_with_defaults(self):
        count = self.bacon.tags.count()
        tag = self.bacon.tags.create(tag="stinky")
        self.assertEqual(count + 1, self.bacon.tags.count())
        tag, created = self.bacon.tags.update_or_create(
            create_defaults={"tag": "uncured"}, defaults={"tag": "juicy"}, id=tag.id
        )
        self.assertIs(created, False)
        self.assertEqual(count + 1, self.bacon.tags.count())
        self.assertEqual(tag.tag, "juicy")