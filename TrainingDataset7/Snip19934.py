def test_app_labeled_name_unknown_model(self):
        ct = ContentType(app_label="contenttypes_tests", model="unknown")
        self.assertEqual(ct.app_labeled_name, "contenttypes_tests | unknown")