def test_update_from_other_field(self):
        p1 = Point(1, 1, srid=4326)
        p2 = Point(2, 2, srid=4326)
        obj = ManyPointModel.objects.create(
            point1=p1,
            point2=p2,
            point3=p2.transform(3857, clone=True),
        )
        # Updating a point to a point of the same SRID.
        ManyPointModel.objects.filter(pk=obj.pk).update(point2=F("point1"))
        obj.refresh_from_db()
        self.assertEqual(obj.point2, p1)
        # Updating a point to a point with a different SRID.
        if connection.features.supports_transform:
            ManyPointModel.objects.filter(pk=obj.pk).update(point3=F("point1"))
            obj.refresh_from_db()
            self.assertTrue(
                obj.point3.equals_exact(p1.transform(3857, clone=True), 0.1)
            )