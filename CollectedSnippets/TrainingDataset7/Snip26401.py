def test_reverse_foreign_key_instance_to_field_caching(self):
        parent = Parent.objects.create(name="a")
        ToFieldChild.objects.create(parent=parent)
        child = parent.to_field_children.get()
        with self.assertNumQueries(0):
            self.assertIs(child.parent, parent)