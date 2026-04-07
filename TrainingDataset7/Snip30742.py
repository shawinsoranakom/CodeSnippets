def test_duplicate_values_list(self):
        value = Number.objects.values_list("num", "num").get()
        self.assertEqual(value, (72, 72))
        value = Number.objects.values_list(F("num"), F("num")).get()
        self.assertEqual(value, (72, 72))