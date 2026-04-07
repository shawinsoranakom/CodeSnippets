def test_many_to_many(self):
        obj = Object.objects.create()
        obj.related_objects.create()
        self.assertEqual(Object.objects.count(), 2)
        self.assertEqual(obj.related_objects.count(), 1)

        intermediary_model = Object._meta.get_field(
            "related_objects"
        ).remote_field.through
        intermediary_model.objects.create(from_object_id=obj.id, to_object_id=12345)
        self.assertEqual(obj.related_objects.count(), 1)
        self.assertEqual(intermediary_model.objects.count(), 2)