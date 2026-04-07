def test_json_response_raises_type_error_with_default_setting(self):
        with self.assertRaisesMessage(
            TypeError,
            "In order to allow non-dict objects to be serialized set the "
            "safe parameter to False",
        ):
            JsonResponse([1, 2, 3])