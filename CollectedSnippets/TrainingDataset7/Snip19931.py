def test_name(self):
        ct = ContentType.objects.get(app_label="contenttypes_tests", model="site")
        self.assertEqual(ct.name, "site")