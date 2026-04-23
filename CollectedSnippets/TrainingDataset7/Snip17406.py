async def test_aupdate_or_create(self):
        instance, created = await SimpleModel.objects.aupdate_or_create(
            id=self.s1.id, defaults={"field": 2}
        )
        self.assertEqual(instance, self.s1)
        self.assertEqual(instance.field, 2)
        self.assertIs(created, False)
        instance, created = await SimpleModel.objects.aupdate_or_create(field=4)
        self.assertEqual(await SimpleModel.objects.acount(), 4)
        self.assertIs(created, True)
        instance, created = await SimpleModel.objects.aupdate_or_create(
            field=5, defaults={"field": 7}, create_defaults={"field": 6}
        )
        self.assertEqual(await SimpleModel.objects.acount(), 5)
        self.assertIs(created, True)
        self.assertEqual(instance.field, 6)