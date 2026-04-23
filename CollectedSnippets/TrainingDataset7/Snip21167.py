def test_19187_values(self):
        msg = "Cannot call delete() after .values() or .values_list()"
        with self.assertRaisesMessage(TypeError, msg):
            Image.objects.values().delete()
        with self.assertRaisesMessage(TypeError, msg):
            Image.objects.values_list().delete()