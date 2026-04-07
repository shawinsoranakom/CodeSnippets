def test_update_values_annotation(self):
        RelatedPoint.objects.annotate(abs_id=Abs("id")).filter(
            data__is_active=False
        ).values("id", "abs_id").update(data=self.d0)
        self.r1.refresh_from_db(fields=["data"])
        self.assertEqual(self.r1.data, self.d0)