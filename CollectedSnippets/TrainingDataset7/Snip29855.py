def test_search_vector(self):
        """SearchVector generates IMMUTABLE SQL in order to be indexable."""
        index_name = "test_search_vector"
        index = Index(SearchVector("id", "scene", config="english"), name=index_name)
        # Indexed function must be IMMUTABLE.
        with connection.schema_editor() as editor:
            editor.add_index(Scene, index)
        constraints = self.get_constraints(Scene._meta.db_table)
        self.assertIn(index_name, constraints)
        self.assertIs(constraints[index_name]["index"], True)

        with connection.schema_editor() as editor:
            editor.remove_index(Scene, index)
        self.assertNotIn(index_name, self.get_constraints(Scene._meta.db_table))