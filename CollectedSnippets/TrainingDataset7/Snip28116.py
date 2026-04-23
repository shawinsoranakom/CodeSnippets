def test_value_from_object_instance_with_pk(self):
        obj = ManyToMany.objects.create()
        related_obj = ManyToMany.objects.create()
        obj.m2m.add(related_obj)
        self.assertEqual(
            obj._meta.get_field("m2m").value_from_object(obj), [related_obj]
        )