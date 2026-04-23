def test_custom_algorithm(self):
        signer = signing.Signer(key="predictable-secret", algorithm="sha512")
        self.assertEqual(
            signer.signature("hello"),
            "Usf3uVQOZ9m6uPfVonKR-EBXjPe7bjMbp3_Fq8MfsptgkkM1ojidN0BxYaT5HAEN1"
            "VzO9_jVu7R-VkqknHYNvw",
        )