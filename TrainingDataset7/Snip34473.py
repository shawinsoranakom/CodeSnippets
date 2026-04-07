def test_explicit_baking(self):
        # explicit baking
        response = self._response()
        self.assertFalse(response.is_rendered)
        response.render()
        self.assertTrue(response.is_rendered)