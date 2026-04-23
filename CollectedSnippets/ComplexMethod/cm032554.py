def test_parser_config(self, HttpApiAuth, add_dataset_func, parser_config):
        dataset_id = add_dataset_func
        payload = {"parser_config": parser_config}
        res = update_dataset(HttpApiAuth, dataset_id, payload)
        assert res["code"] == 0, res

        res = list_datasets(HttpApiAuth)
        assert res["code"] == 0, res
        for k, v in parser_config.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    assert res["data"][0]["parser_config"][k][kk] == vv, res
            else:
                assert res["data"][0]["parser_config"][k] == v, res