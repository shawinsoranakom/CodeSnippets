def test_app_labeled_name(self):
        ct = ContentType.objects.get(app_label="contenttypes_tests", model="site")
        self.assertEqual(ct.app_labeled_name, "Contenttypes_Tests | site")