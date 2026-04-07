def test_init(self):
        """
        Test initialization of distance models.
        """
        self.assertEqual(9, SouthTexasCity.objects.count())
        self.assertEqual(9, SouthTexasCityFt.objects.count())
        self.assertEqual(11, AustraliaCity.objects.count())
        self.assertEqual(4, SouthTexasZipcode.objects.count())
        self.assertEqual(4, CensusZipcode.objects.count())
        self.assertEqual(1, Interstate.objects.count())
        self.assertEqual(1, SouthTexasInterstate.objects.count())