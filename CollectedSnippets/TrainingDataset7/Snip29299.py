def assert_get_place(**params):
            self.assertEqual(
                repr(Place.objects.get(**params)), "<Place: Demon Dogs the place>"
            )