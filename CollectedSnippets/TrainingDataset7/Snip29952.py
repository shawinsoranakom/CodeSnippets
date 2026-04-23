def test_serialize_range_with_null(self):
        instance = RangesModel(ints=NumericRange(None, 10))
        data = serializers.serialize("json", [instance])
        new_instance = list(serializers.deserialize("json", data))[0].object
        self.assertEqual(new_instance.ints, NumericRange(None, 10))

        instance = RangesModel(ints=NumericRange(10, None))
        data = serializers.serialize("json", [instance])
        new_instance = list(serializers.deserialize("json", data))[0].object
        self.assertEqual(new_instance.ints, NumericRange(10, None))