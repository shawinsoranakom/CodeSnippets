def test_index_name(self):
        if not self.has_spatial_indexes(City._meta.db_table):
            self.skipTest("Spatial indexes in Meta.indexes are not supported.")
        index_name = "custom_point_index_name"
        index = Index(fields=["point"], name=index_name)
        with connection.schema_editor() as editor:
            editor.add_index(City, index)
            indexes = self.get_indexes(City._meta.db_table)
            self.assertIn(index_name, indexes)
            self.assertEqual(indexes[index_name], ["point"])
            editor.remove_index(City, index)