def test_set_querycount(self):
        policy = Policy.objects.create()
        version = Version.objects.create(policy=policy)
        location = Location.objects.create(version=version)
        Item.objects.create(
            version=version,
            location=location,
            location_value=location,
        )
        # 2 UPDATEs for SET of item values and one for DELETE locations.
        with self.assertNumQueries(3):
            location.delete()