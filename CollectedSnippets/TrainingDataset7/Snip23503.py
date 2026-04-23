async def test_generic_async_aupdate_or_create(self):
        tag, created = await self.bacon.tags.aupdate_or_create(
            id=self.fatty.id, defaults={"tag": "orange"}
        )
        self.assertIs(created, False)
        self.assertEqual(tag.tag, "orange")
        self.assertEqual(await self.bacon.tags.acount(), 2)
        tag, created = await self.bacon.tags.aupdate_or_create(tag="pink")
        self.assertIs(created, True)
        self.assertEqual(await self.bacon.tags.acount(), 3)
        self.assertEqual(tag.tag, "pink")