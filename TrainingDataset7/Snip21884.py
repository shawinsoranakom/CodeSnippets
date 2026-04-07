def test_custom_get_available_name(self):
        first = self.storage.save("custom_storage", ContentFile("custom contents"))
        self.assertEqual(first, "custom_storage")
        second = self.storage.save("custom_storage", ContentFile("more contents"))
        self.assertEqual(second, "custom_storage.2")
        self.storage.delete(first)
        self.storage.delete(second)