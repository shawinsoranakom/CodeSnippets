def test_createnull(self):
        "Testing creating a model instance and the geometry being None"
        c = City()
        self.assertIsNone(c.point)