def test_cached_foreign_key_with_to_field_not_cleared_by_save(self):
        parent = Parent.objects.create(name="a")
        child = ToFieldChild.objects.create(parent=parent)
        with self.assertNumQueries(0):
            self.assertIs(child.parent, parent)