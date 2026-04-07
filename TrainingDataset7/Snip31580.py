def test_select_related_after_values_list(self):
        """
        Running select_related() after calling values_list() raises a TypeError
        """
        message = "Cannot call select_related() after .values() or .values_list()"
        with self.assertRaisesMessage(TypeError, message):
            list(Species.objects.values_list("name").select_related("genus"))