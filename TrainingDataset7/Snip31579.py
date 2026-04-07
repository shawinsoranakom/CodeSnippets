def test_select_related_after_values(self):
        """
        Running select_related() after calling values() raises a TypeError
        """
        message = "Cannot call select_related() after .values() or .values_list()"
        with self.assertRaisesMessage(TypeError, message):
            list(Species.objects.values("name").select_related("genus"))