def test_nullable_loading(self):
        instance = list(serializers.deserialize("json", self.nullable_test_data))[
            0
        ].object
        self.assertIsNone(instance.field)