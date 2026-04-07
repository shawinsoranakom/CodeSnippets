def test_str(self):
        ct = ContentType.objects.get(app_label="contenttypes_tests", model="site")
        self.assertEqual(str(ct), "Contenttypes_Tests | site")