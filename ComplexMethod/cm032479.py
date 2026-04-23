def test_parser_config(self, client, add_dataset_func, parser_config):
        dataset = add_dataset_func
        dataset.update({"parser_config": parser_config})
        for k, v in parser_config.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    assert attrgetter(f"{k}.{kk}")(dataset.parser_config) == vv, str(dataset)
            else:
                assert attrgetter(k)(dataset.parser_config) == v, str(dataset)

        retrieved_dataset = client.get_dataset(name=dataset.name)
        for k, v in parser_config.items():
            if isinstance(v, dict):
                for kk, vv in v.items():
                    assert attrgetter(f"{k}.{kk}")(retrieved_dataset.parser_config) == vv, str(retrieved_dataset)
            else:
                assert attrgetter(k)(retrieved_dataset.parser_config) == v, str(retrieved_dataset)