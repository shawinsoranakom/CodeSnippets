def test_empty_fields_to_construct_instance(self):
        """
        No fields should be set on a model instance if construct_instance
        receives fields=().
        """
        form = modelform_factory(Person, fields="__all__")({"name": "John Doe"})
        self.assertTrue(form.is_valid())
        instance = construct_instance(form, Person(), fields=())
        self.assertEqual(instance.name, "")