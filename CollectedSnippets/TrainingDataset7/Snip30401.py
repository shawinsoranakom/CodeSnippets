def test_database_routing_batch_atomicity(self):
        f1 = Food.objects.create(name="Banana")
        f2 = Food.objects.create(name="Apple")
        f1.name = "Kiwi"
        f2.name = "Kiwi"
        with self.assertRaises(IntegrityError):
            Food.objects.bulk_update([f1, f2], fields=["name"], batch_size=1)
        self.assertIs(Food.objects.filter(name="Kiwi").exists(), False)