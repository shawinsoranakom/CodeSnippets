def test_abstract_children(self):
        index_names = [index.name for index in ChildModel1._meta.indexes]
        self.assertEqual(
            index_names,
            ["model_index_name_440998_idx", "model_indexes_childmodel1_idx"],
        )
        index_names = [index.name for index in ChildModel2._meta.indexes]
        self.assertEqual(
            index_names,
            ["model_index_name_b6c374_idx", "model_indexes_childmodel2_idx"],
        )