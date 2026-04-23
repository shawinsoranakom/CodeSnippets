def assert_python_contains_datetime(self, objects, dt):
        self.assertEqual(objects[0]["fields"]["dt"], dt)