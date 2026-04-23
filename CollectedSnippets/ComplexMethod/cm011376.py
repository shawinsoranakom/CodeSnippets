def process_value(
                target_value: Any, source_value: Any, key_path: str
            ) -> Any:
                source_type = type(source_value)
                if source_type is torch._subclasses.fake_tensor.FakeTensor:
                    source_type = torch.Tensor
                if target_value is not None and not isinstance(
                    target_value, source_type
                ):
                    raise RuntimeError(
                        f"Target value {key_path} is set to {type(target_value)}, but source value is {type(source_value)}"
                    )
                if isinstance(source_value, torch.Tensor):
                    return load_tensor(target_value, source_value, key_path)
                elif isinstance(source_value, dict):
                    if target_value is None:
                        # create a new map with all the keys present in source_value
                        target_value = dict.fromkeys(source_value.keys())

                    # pyrefly: ignore [missing-attribute]
                    for key in list(target_value.keys()):
                        current_path = f"{key_path}.{key}" if key_path else key
                        if key in source_value:
                            target_value[key] = process_value(
                                target_value[key], source_value[key], current_path
                            )
                        else:
                            missing_keys.append(current_path)

                    return target_value
                elif isinstance(source_value, list):
                    if target_value is None:
                        target_value = [None] * len(source_value)
                    result = []
                    for i, (target_item, source_item) in enumerate(
                        zip_longest(target_value, source_value, fillvalue=None)
                    ):
                        current_path = f"{key_path}[{i}]" if key_path else f"[{i}]"
                        result.append(
                            process_value(target_item, source_item, current_path)
                        )
                    return result
                else:
                    return source_value