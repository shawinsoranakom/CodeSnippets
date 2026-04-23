def test_remove_after_prefetch(self):
        c = City.objects.create(name="Musical City")
        d = District.objects.create(name="Ladida", city=c)
        city = City.objects.prefetch_related("districts").get(id=c.id)
        self.assertSequenceEqual(city.districts.all(), [d])
        city.districts.remove(d)
        self.assertSequenceEqual(city.districts.all(), [])