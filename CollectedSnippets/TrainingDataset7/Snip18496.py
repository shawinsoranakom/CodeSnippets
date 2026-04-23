def test_circular_reference(self):
        # deserialize_db_from_string() handles circular references.
        data = """
        [
            {
                "model": "backends.object",
                "pk": 1,
                "fields": {"obj_ref": 1, "related_objects": []}
            },
            {
                "model": "backends.objectreference",
                "pk": 1,
                "fields": {"obj": 1}
            }
        ]
        """
        connection.creation.deserialize_db_from_string(data)
        obj = Object.objects.get()
        obj_ref = ObjectReference.objects.get()
        self.assertEqual(obj.obj_ref, obj_ref)
        self.assertEqual(obj_ref.obj, obj)