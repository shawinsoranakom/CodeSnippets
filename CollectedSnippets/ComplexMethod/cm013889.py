def get_torch_obj_rule_map() -> dict[Any, type["VariableTracker"]]:
    d: dict[Any, type[VariableTracker]] = {}
    for m in torch_name_rule_map:
        for k, v in m.items():  # type: ignore[attr-defined]
            if ".py#" not in k:
                obj = load_object(k)
            else:
                torch_dir = _module_dir(torch)
                if torch_dir is None:
                    continue
                obj = torch_dir + k[len("torch/") :]
            if obj is not None:
                if is_lru_cache_wrapped_function(obj):
                    obj = obj.__wrapped__
                if obj in d and d[obj] != v:
                    raise AssertionError(
                        f"Duplicate torch object {obj} with different rules: {v}, {d[obj]}"
                    )
                else:
                    d[obj] = v
    return d