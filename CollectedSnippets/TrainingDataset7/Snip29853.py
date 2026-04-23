def test_gist_include(self):
        index_name = "scene_gist_include_setting"
        index = GistIndex(name=index_name, fields=["scene"], include=["setting"])
        with connection.schema_editor() as editor:
            editor.add_index(Scene, index)
        constraints = self.get_constraints(Scene._meta.db_table)
        self.assertIn(index_name, constraints)
        self.assertEqual(constraints[index_name]["type"], GistIndex.suffix)
        self.assertEqual(constraints[index_name]["columns"], ["scene", "setting"])
        with connection.schema_editor() as editor:
            editor.remove_index(Scene, index)
        self.assertNotIn(index_name, self.get_constraints(Scene._meta.db_table))