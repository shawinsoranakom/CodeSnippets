def test_integerchoices_empty_label(self):
        self.assertEqual(Vehicle.choices[0], (None, "(Unknown)"))
        self.assertEqual(Vehicle.labels[0], "(Unknown)")
        self.assertIsNone(Vehicle.values[0])
        self.assertEqual(Vehicle.names[0], "__empty__")