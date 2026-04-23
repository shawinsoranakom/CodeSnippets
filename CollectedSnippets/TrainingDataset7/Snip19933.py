def test_name_unknown_model(self):
        ct = ContentType(app_label="contenttypes_tests", model="unknown")
        self.assertEqual(ct.name, "unknown")