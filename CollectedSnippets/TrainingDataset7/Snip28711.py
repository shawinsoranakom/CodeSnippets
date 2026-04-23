def test_inherited_not_updated_exception(self):
        # NotUpdated is also inherited.
        obj = Restaurant(id=999)
        with self.assertRaises(Place.NotUpdated):
            obj.save(update_fields={"name"})