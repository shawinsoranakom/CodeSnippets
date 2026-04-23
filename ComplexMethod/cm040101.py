def from_config(cls, config, custom_objects=None, safe_mode=None):
        safe_mode = safe_mode or serialization_lib.in_safe_mode()
        fn_config = config["function"]
        if (
            isinstance(fn_config, dict)
            and "class_name" in fn_config
            and fn_config["class_name"] == "__lambda__"
        ):
            cls._raise_for_lambda_deserialization(safe_mode)
            inner_config = fn_config["config"]
            fn = python_utils.func_load(
                inner_config["code"],
                defaults=inner_config["defaults"],
                closure=inner_config["closure"],
            )
            config["function"] = fn
        else:
            config["function"] = serialization_lib.deserialize_keras_object(
                fn_config, custom_objects=custom_objects
            )
        if "output_shape" in config:
            fn_config = config["output_shape"]
            if (
                isinstance(fn_config, dict)
                and "class_name" in fn_config
                and fn_config["class_name"] == "__lambda__"
            ):
                cls._raise_for_lambda_deserialization(safe_mode)
                inner_config = fn_config["config"]
                fn = python_utils.func_load(
                    inner_config["code"],
                    defaults=inner_config["defaults"],
                    closure=inner_config["closure"],
                )
                config["output_shape"] = fn
            else:
                output_shape = serialization_lib.deserialize_keras_object(
                    fn_config, custom_objects=custom_objects
                )
                if isinstance(output_shape, list) and all(
                    isinstance(e, (int, type(None))) for e in output_shape
                ):
                    output_shape = tuple(output_shape)
                config["output_shape"] = output_shape

        if "arguments" in config:
            config["arguments"] = serialization_lib.deserialize_keras_object(
                config["arguments"], custom_objects=custom_objects
            )
        return cls(**config)