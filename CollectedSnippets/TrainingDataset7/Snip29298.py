def assert_get_restaurant(**params):
            self.assertEqual(
                repr(Restaurant.objects.get(**params)),
                "<Restaurant: Demon Dogs the restaurant>",
            )