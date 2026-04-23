def test_generic_update_or_create_when_created_with_create_defaults(self):
        count = self.bacon.tags.count()
        tag, created = self.bacon.tags.update_or_create(
            # Since, the "stinky" tag doesn't exist create
            # a "juicy" tag.
            create_defaults={"tag": "juicy"},
            defaults={"tag": "uncured"},
            tag="stinky",
        )
        self.assertEqual(tag.tag, "juicy")
        self.assertIs(created, True)
        self.assertEqual(count + 1, self.bacon.tags.count())