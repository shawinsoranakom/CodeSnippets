async def test_generic_async_aupdate_or_create_with_create_defaults(self):
        tag, created = await self.bacon.tags.aupdate_or_create(
            id=self.fatty.id,
            create_defaults={"tag": "pink"},
            defaults={"tag": "orange"},
        )
        self.assertIs(created, False)
        self.assertEqual(tag.tag, "orange")
        self.assertEqual(await self.bacon.tags.acount(), 2)
        tag, created = await self.bacon.tags.aupdate_or_create(
            tag="pink", create_defaults={"tag": "brown"}
        )
        self.assertIs(created, True)
        self.assertEqual(await self.bacon.tags.acount(), 3)
        self.assertEqual(tag.tag, "brown")