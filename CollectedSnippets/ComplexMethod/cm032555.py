def test_field_unset(self, HttpApiAuth, add_dataset_func):
        dataset_id = add_dataset_func
        res = list_datasets(HttpApiAuth)
        assert res["code"] == 0, res
        original_data = res["data"][0]

        payload = {"name": "default_unset"}
        res = update_dataset(HttpApiAuth, dataset_id, payload)
        assert res["code"] == 0, res

        res = list_datasets(HttpApiAuth)
        assert res["code"] == 0, res
        assert res["data"][0]["avatar"] == original_data["avatar"], res
        assert res["data"][0]["description"] == original_data["description"], res
        assert res["data"][0]["embedding_model"] == original_data["embedding_model"], res
        assert res["data"][0]["permission"] == original_data["permission"], res
        assert res["data"][0]["chunk_method"] == original_data["chunk_method"], res
        assert res["data"][0]["pagerank"] == original_data["pagerank"], res
        assert res["data"][0]["parser_config"] == original_data["parser_config"], res