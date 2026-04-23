def assert_yaml_contains_datetime(self, yaml, dt):
        # Depending on the yaml dumper, '!timestamp' might be absent
        self.assertRegex(yaml, r"\n  fields: {dt: !(!timestamp)? '%s'}" % re.escape(dt))