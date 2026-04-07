def test_update_with_expression(self):
        city = City.objects.create(point=Point(1, 1, srid=4326))
        City.objects.filter(pk=city.pk).update(point=functions.Translate("point", 1, 1))
        city.refresh_from_db()
        self.assertEqual(city.point, Point(2, 2, srid=4326))