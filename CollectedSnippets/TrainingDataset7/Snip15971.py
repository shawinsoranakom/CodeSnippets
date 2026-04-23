def test_flatten_fieldsets(self):
        """
        Regression test for #18051
        """
        fieldsets = ((None, {"fields": ("url", "title", ("content", "sites"))}),)
        self.assertEqual(
            flatten_fieldsets(fieldsets), ["url", "title", "content", "sites"]
        )

        fieldsets = ((None, {"fields": ("url", "title", ["content", "sites"])}),)
        self.assertEqual(
            flatten_fieldsets(fieldsets), ["url", "title", "content", "sites"]
        )