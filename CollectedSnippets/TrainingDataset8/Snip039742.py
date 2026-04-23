def test_get_type_name(self, obj: object, expected_type: str):
        """Test getting the type name via _get_type_name"""
        self.assertEqual(metrics_util._get_type_name(obj), expected_type)