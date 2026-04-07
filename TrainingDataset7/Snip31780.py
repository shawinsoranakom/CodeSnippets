def test_pkless_serialized_strings(self):
        """
        Serialized strings without PKs can be turned into models
        """
        deserial_objs = list(
            serializers.deserialize(self.serializer_name, self.pkless_str)
        )
        for obj in deserial_objs:
            self.assertFalse(obj.object.id)
            obj.save()
        self.assertEqual(Category.objects.count(), 5)