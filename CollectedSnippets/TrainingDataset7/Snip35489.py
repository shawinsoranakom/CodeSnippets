def assert_json_contains_datetime(self, json, dt):
        self.assertIn('"fields": {"dt": "%s"}' % dt, json)