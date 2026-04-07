def test_filter_on_parent_returns_object_of_parent_type(self):
        # Filters against the parent model return objects of the parent's type.
        p = Place.objects.get(name="Demon Dogs")
        self.assertIs(type(p), Place)