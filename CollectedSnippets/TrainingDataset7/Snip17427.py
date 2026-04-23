async def test_aupdate_or_create(self):
        new_simple, created = await self.mtm1.simples.aupdate_or_create(field=2)
        self.assertIs(created, True)
        self.assertEqual(await self.mtm1.simples.acount(), 1)
        self.assertEqual(new_simple.field, 2)
        new_simple1, created = await self.mtm1.simples.aupdate_or_create(
            id=new_simple.id, defaults={"field": 3}
        )
        self.assertIs(created, False)
        self.assertEqual(new_simple1.field, 3)

        new_simple2, created = await self.mtm1.simples.aupdate_or_create(
            field=4, defaults={"field": 6}, create_defaults={"field": 5}
        )
        self.assertIs(created, True)
        self.assertEqual(new_simple2.field, 5)
        self.assertEqual(await self.mtm1.simples.acount(), 2)