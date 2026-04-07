def test_values(self):
        msg = "Cannot call QuerySet.contains() after .values() or .values_list()."
        with self.assertRaisesMessage(TypeError, msg):
            DumbCategory.objects.values_list("pk").contains(self.category)
        with self.assertRaisesMessage(TypeError, msg):
            DumbCategory.objects.values("pk").contains(self.category)