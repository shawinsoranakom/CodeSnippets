def test_deserialized_object_repr(self):
        deserial_obj = DeserializedObject(obj=self.jane)
        self.assertEqual(
            repr(deserial_obj), "<DeserializedObject: serializers.Author(pk=1)>"
        )