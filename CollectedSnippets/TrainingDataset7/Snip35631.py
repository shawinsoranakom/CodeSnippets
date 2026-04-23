def test_update_multiple_objects(self):
        """
        We can update multiple objects at once.
        """
        resp = DataPoint.objects.filter(value="banana").update(value="pineapple")
        self.assertEqual(resp, 2)
        self.assertEqual(DataPoint.objects.get(name="d2").value, "pineapple")