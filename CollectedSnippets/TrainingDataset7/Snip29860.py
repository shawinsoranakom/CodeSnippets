def test_spgist_include(self):
        index_name = "scene_spgist_include_setting"
        index = SpGistIndex(name=index_name, fields=["scene"], include=["setting"])
        with connection.schema_editor() as editor:
            editor.add_index(Scene, index)
        constraints = self.get_constraints(Scene._meta.db_table)
        self.assertIn(index_name, constraints)
        self.assertEqual(constraints[index_name]["type"], SpGistIndex.suffix)
        self.assertEqual(constraints[index_name]["columns"], ["scene", "setting"])
        with connection.schema_editor() as editor:
            editor.remove_index(Scene, index)
        self.assertNotIn(index_name, self.get_constraints(Scene._meta.db_table))