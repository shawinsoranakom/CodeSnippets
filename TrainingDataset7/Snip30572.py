def test_ticket7323(self):
        self.assertEqual(Item.objects.values("creator", "name").count(), 4)