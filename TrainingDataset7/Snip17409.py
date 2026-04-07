async def test_abulk_update(self):
        instances = SimpleModel.objects.all()
        async for instance in instances:
            instance.field = instance.field * 10

        await SimpleModel.objects.abulk_update(instances, ["field"])

        qs = [(o.pk, o.field) async for o in SimpleModel.objects.all()]
        self.assertCountEqual(
            qs,
            [(self.s1.pk, 10), (self.s2.pk, 20), (self.s3.pk, 30)],
        )