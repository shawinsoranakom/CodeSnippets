def test_create_after_prefetch(self):
        c = City.objects.create(name="Musical City")
        d1 = District.objects.create(name="Ladida", city=c)
        city = City.objects.prefetch_related("districts").get(id=c.id)
        self.assertSequenceEqual(city.districts.all(), [d1])
        d2 = city.districts.create(name="Goa")
        self.assertSequenceEqual(city.districts.all(), [d1, d2])