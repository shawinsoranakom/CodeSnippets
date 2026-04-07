def test_update_fk(self):
        """
        Foreign key fields can also be updated, although you can only update
        the object referred to, not anything inside the related object.
        """
        resp = RelatedPoint.objects.filter(name="r1").update(data=self.d0)
        self.assertEqual(resp, 1)
        resp = RelatedPoint.objects.filter(data__name="d0")
        self.assertEqual(list(resp), [self.r1])