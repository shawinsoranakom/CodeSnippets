def test_unicode_serialization(self):
        unicode_name = "יוניקוד"
        data = serializers.serialize(self.serializer_name, [Author(name=unicode_name)])
        self.assertIn(unicode_name, data)
        objs = list(serializers.deserialize(self.serializer_name, data))
        self.assertEqual(objs[0].object.name, unicode_name)