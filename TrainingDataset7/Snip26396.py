def test_add_after_prefetch(self):
        c = City.objects.create(name="Musical City")
        District.objects.create(name="Ladida", city=c)
        d2 = District.objects.create(name="Ladidu")
        city = City.objects.prefetch_related("districts").get(id=c.id)
        self.assertEqual(city.districts.count(), 1)
        city.districts.add(d2)
        self.assertEqual(city.districts.count(), 2)