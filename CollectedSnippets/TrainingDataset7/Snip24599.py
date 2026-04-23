def test_distance_field_deepcopy(self):
        field = DistanceField(None)
        self.assertEqual(copy.deepcopy(field), field)