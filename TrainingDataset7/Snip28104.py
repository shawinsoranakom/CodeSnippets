def test_custom_jsonnull_encoder(self):
        obj = JSONNullDefaultModel.objects.create(
            value={"name": JSONNull(), "array": [1, JSONNull()]}
        )
        obj.refresh_from_db()
        self.assertIsNone(obj.value["name"])
        self.assertEqual(obj.value["array"], [1, None])