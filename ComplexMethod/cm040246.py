def from_config(cls, config, custom_objects=None):
        if "name" in config:
            name = config["name"]
            build_input_shape = config.get("build_input_shape")
            layer_configs = config["layers"]
        else:
            name = None
            layer_configs = config
        model = cls(name=name)
        for layer_config in layer_configs:
            if "module" not in layer_config:
                # Legacy format deserialization (no "module" key)
                # used for H5 and SavedModel formats
                layer = saving_utils.model_from_config(
                    layer_config,
                    custom_objects=custom_objects,
                )
            else:
                layer = serialization_lib.deserialize_keras_object(
                    layer_config,
                    custom_objects=custom_objects,
                )
            model.add(layer)
        if (
            not model._functional
            and "build_input_shape" in locals()
            and build_input_shape
            and isinstance(build_input_shape, (tuple, list))
        ):
            model.build(build_input_shape)
        return model