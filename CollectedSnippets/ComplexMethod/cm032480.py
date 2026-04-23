def test_field_unset(self, client, add_dataset_func):
        dataset = add_dataset_func
        original_dataset = client.get_dataset(name=dataset.name)

        dataset.update({"name": "default_unset"})

        updated_dataset = client.get_dataset(name="default_unset")
        assert updated_dataset.avatar == original_dataset.avatar, str(updated_dataset)
        assert updated_dataset.description == original_dataset.description, str(updated_dataset)
        assert updated_dataset.embedding_model == original_dataset.embedding_model, str(updated_dataset)
        assert updated_dataset.permission == original_dataset.permission, str(updated_dataset)
        assert updated_dataset.chunk_method == original_dataset.chunk_method, str(updated_dataset)
        assert updated_dataset.pagerank == original_dataset.pagerank, str(updated_dataset)
        assert str(updated_dataset.parser_config) == str(original_dataset.parser_config), str(updated_dataset)