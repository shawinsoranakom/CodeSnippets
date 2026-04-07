async def test_aget_or_create(self):
        new_simple, created = await self.mtm1.simples.aget_or_create(field=2)
        self.assertIs(created, True)
        self.assertEqual(await self.mtm1.simples.acount(), 1)
        self.assertEqual(new_simple.field, 2)
        new_simple, created = await self.mtm1.simples.aget_or_create(
            id=new_simple.id, through_defaults={"field": 3}
        )
        self.assertIs(created, False)
        self.assertEqual(await self.mtm1.simples.acount(), 1)
        self.assertEqual(new_simple.field, 2)