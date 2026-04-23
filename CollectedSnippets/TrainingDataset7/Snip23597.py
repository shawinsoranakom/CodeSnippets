def test_ticket_22982(self):
        place = Place.objects.create(name="My Place")
        self.assertIn("GenericRelatedObjectManager", str(place.links))