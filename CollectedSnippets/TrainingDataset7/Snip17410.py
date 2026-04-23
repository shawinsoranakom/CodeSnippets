async def test_ain_bulk(self):
        res = await SimpleModel.objects.ain_bulk()
        self.assertEqual(
            res,
            {self.s1.pk: self.s1, self.s2.pk: self.s2, self.s3.pk: self.s3},
        )

        res = await SimpleModel.objects.ain_bulk([self.s2.pk])
        self.assertEqual(res, {self.s2.pk: self.s2})

        res = await SimpleModel.objects.ain_bulk([self.s2.pk], field_name="id")
        self.assertEqual(res, {self.s2.pk: self.s2})