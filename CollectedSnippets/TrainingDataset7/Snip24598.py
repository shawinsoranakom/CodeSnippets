def test_area_field_deepcopy(self):
        field = AreaField(None)
        self.assertEqual(copy.deepcopy(field), field)