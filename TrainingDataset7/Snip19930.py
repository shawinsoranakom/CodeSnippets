def test_str_auth(self):
        ct = ContentType.objects.get(app_label="auth", model="group")
        self.assertEqual(str(ct), "Authentication and Authorization | group")