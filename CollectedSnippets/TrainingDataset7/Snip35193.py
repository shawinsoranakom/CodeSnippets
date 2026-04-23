def test_book_name_deutsh(self):
        self.assertEqual(self.car.name, "Volkswagen Beetle")
        self.car.name = "VW sKäfer"
        self.car.save()