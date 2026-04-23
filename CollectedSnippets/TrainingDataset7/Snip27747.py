def test_integerchoices_auto_label(self):
        self.assertEqual(Vehicle.CAR.label, "Carriage")
        self.assertEqual(Vehicle.TRUCK.label, "Truck")
        self.assertEqual(Vehicle.JET_SKI.label, "Jet Ski")