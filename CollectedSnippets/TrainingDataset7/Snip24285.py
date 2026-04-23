def test_extent_with_limit(self):
        """
        Testing if extent supports limit.
        """
        extent1 = City.objects.aggregate(Extent("point"))["point__extent"]
        extent2 = City.objects.all()[:3].aggregate(Extent("point"))["point__extent"]
        self.assertNotEqual(extent1, extent2)