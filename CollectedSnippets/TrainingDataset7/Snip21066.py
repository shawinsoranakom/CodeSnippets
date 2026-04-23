def test_only_reverse_many_to_many_ignored(self):
        location = Location.objects.create()
        request = Request.objects.create(location=location)
        item = Item.objects.create(value=1)
        request.items.add(item)
        with self.assertNumQueries(1):
            self.assertEqual(Item.objects.only("request").get(), item)