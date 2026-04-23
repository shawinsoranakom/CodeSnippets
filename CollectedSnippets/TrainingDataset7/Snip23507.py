async def test_generic_async_aget_or_create(self):
        tag, created = await self.bacon.tags.aget_or_create(
            id=self.fatty.id, defaults={"tag": "orange"}
        )
        self.assertIs(created, False)
        self.assertEqual(tag.tag, "fatty")
        self.assertEqual(await self.bacon.tags.acount(), 2)
        tag, created = await self.bacon.tags.aget_or_create(tag="orange")
        self.assertIs(created, True)
        self.assertEqual(await self.bacon.tags.acount(), 3)
        self.assertEqual(tag.tag, "orange")