def test_blank_string_saved_as_null(self):
        o = GenericIPAddress.objects.create(ip="")
        o.refresh_from_db()
        self.assertIsNone(o.ip)
        GenericIPAddress.objects.update(ip="")
        o.refresh_from_db()
        self.assertIsNone(o.ip)