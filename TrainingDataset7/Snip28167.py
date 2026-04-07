def test_to_python(self):
        self.assertIsNone(models.UUIDField().to_python(None))