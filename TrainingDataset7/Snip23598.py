def test_filter_on_related_proxy_model(self):
        place = Place.objects.create()
        Link.objects.create(content_object=place)
        self.assertEqual(Place.objects.get(link_proxy__object_id=place.id), place)