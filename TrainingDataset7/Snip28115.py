def test_value_from_object_instance_without_pk(self):
        obj = ManyToMany()
        self.assertEqual(obj._meta.get_field("m2m").value_from_object(obj), [])