def test_defer_of_overridden_scalar(self):
        ShadowChild.objects.create()
        obj = ShadowChild.objects.defer("name").get()
        self.assertEqual(obj.name, "adonis")