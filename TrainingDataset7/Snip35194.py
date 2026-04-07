def test_book_name_french(self):
        self.assertEqual(self.car.name, "Volkswagen Beetle")
        self.car.name = "Volkswagen Coccinelle"
        self.car.save()