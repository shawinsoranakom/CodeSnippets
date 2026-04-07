def test_float_serialization(self):
        """Float values serialize and deserialize intact"""
        sc = Score(score=3.4)
        sc.save()
        serial_str = serializers.serialize(self.serializer_name, [sc])
        deserial_objs = list(serializers.deserialize(self.serializer_name, serial_str))
        self.assertEqual(deserial_objs[0].object.score, Approximate(3.4, places=1))