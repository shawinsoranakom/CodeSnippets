async def test_aget_object_or_404(self):
        self.assertEqual(await aget_object_or_404(SimpleModel, field=1), self.s2)
        self.assertEqual(await aget_object_or_404(SimpleModel, Q(field=0)), self.s1)
        self.assertEqual(
            await aget_object_or_404(SimpleModel.objects.all(), field=1), self.s2
        )
        self.assertEqual(
            await aget_object_or_404(self.s1.relatedmodel_set, pk=self.r1.pk), self.r1
        )
        # Http404 is returned if the list is empty.
        msg = "No SimpleModel matches the given query."
        with self.assertRaisesMessage(Http404, msg):
            await aget_object_or_404(SimpleModel, field=2)