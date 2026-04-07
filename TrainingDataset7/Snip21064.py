def test_only_many_to_many_ignored(self):
        location = Location.objects.create()
        request = Request.objects.create(location=location)
        with self.assertNumQueries(1):
            self.assertEqual(Request.objects.only("items").get(), request)