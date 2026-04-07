def test_is_picklable_with_non_picklable_object(self):
        unpicklable_obj = UnpicklableObject()
        self.assertEqual(is_pickable(unpicklable_obj), False)