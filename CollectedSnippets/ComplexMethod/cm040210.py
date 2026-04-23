def deserialize_keras_object(
    config, custom_objects=None, safe_mode=True, **kwargs
):
    """Retrieve the object by deserializing the config dict.

    The config dict is a Python dictionary that consists of a set of key-value
    pairs, and represents a Keras object, such as an `Optimizer`, `Layer`,
    `Metrics`, etc. The saving and loading library uses the following keys to
    record information of a Keras object:

    - `class_name`: String. This is the name of the class,
      as exactly defined in the source
      code, such as "LossesContainer".
    - `config`: Dict. Library-defined or user-defined key-value pairs that store
      the configuration of the object, as obtained by `object.get_config()`.
    - `module`: String. The path of the python module. Built-in Keras classes
      expect to have prefix `keras`.
    - `registered_name`: String. The key the class is registered under via
      `keras.saving.register_keras_serializable(package, name)` API. The
      key has the format of '{package}>{name}', where `package` and `name` are
      the arguments passed to `register_keras_serializable()`. If `name` is not
      provided, it uses the class name. If `registered_name` successfully
      resolves to a class (that was registered), the `class_name` and `config`
      values in the dict will not be used. `registered_name` is only used for
      non-built-in classes.

    For example, the following dictionary represents the built-in Adam optimizer
    with the relevant config:

    ```python
    dict_structure = {
        "class_name": "Adam",
        "config": {
            "amsgrad": false,
            "beta_1": 0.8999999761581421,
            "beta_2": 0.9990000128746033,
            "decay": 0.0,
            "epsilon": 1e-07,
            "learning_rate": 0.0010000000474974513,
            "name": "Adam"
        },
        "module": "keras.optimizers",
        "registered_name": None
    }
    # Returns an `Adam` instance identical to the original one.
    deserialize_keras_object(dict_structure)
    ```

    If the class does not have an exported Keras namespace, the library tracks
    it by its `module` and `class_name`. For example:

    ```python
    dict_structure = {
      "class_name": "MetricsList",
      "config": {
          ...
      },
      "module": "keras.trainers.compile_utils",
      "registered_name": "MetricsList"
    }

    # Returns a `MetricsList` instance identical to the original one.
    deserialize_keras_object(dict_structure)
    ```

    And the following dictionary represents a user-customized `MeanSquaredError`
    loss:

    ```python
    @keras.saving.register_keras_serializable(package='my_package')
    class ModifiedMeanSquaredError(keras.losses.MeanSquaredError):
      ...

    dict_structure = {
        "class_name": "ModifiedMeanSquaredError",
        "config": {
            "fn": "mean_squared_error",
            "name": "mean_squared_error",
            "reduction": "auto"
        },
        "registered_name": "my_package>ModifiedMeanSquaredError"
    }
    # Returns the `ModifiedMeanSquaredError` object
    deserialize_keras_object(dict_structure)
    ```

    Args:
        config: Python dict describing the object.
        custom_objects: Python dict containing a mapping between custom
            object names the corresponding classes or functions.
        safe_mode: Boolean, defaults to False. If True, disables unsafe
            lambda deserialization.

            Note that safe_mode is designed to protect against code
            serialized within the Keras model file being loaded. It does
            not provide isolation from the local Python environment and
            does not guard against modifications made outside of the
            serialized file.

    Returns:
        The object described by the `config` dictionary.
    """
    safe_scope_arg = in_safe_mode()  # Enforces SafeModeScope
    safe_mode = safe_scope_arg if safe_scope_arg is not None else safe_mode

    module_objects = kwargs.pop("module_objects", None)
    custom_objects = custom_objects or {}
    tlco = global_state.get_global_attribute("custom_objects_scope_dict", {})
    gco = object_registration.GLOBAL_CUSTOM_OBJECTS
    custom_objects = {**custom_objects, **tlco, **gco}

    if config is None:
        return None

    if (
        isinstance(config, str)
        and custom_objects
        and custom_objects.get(config) is not None
    ):
        # This is to deserialize plain functions which are serialized as
        # string names by legacy saving formats.
        return custom_objects[config]

    if isinstance(config, (list, tuple)):
        return [
            deserialize_keras_object(
                x, custom_objects=custom_objects, safe_mode=safe_mode
            )
            for x in config
        ]

    if module_objects is not None:
        inner_config, fn_module_name, has_custom_object = None, None, False

        if isinstance(config, dict):
            if "config" in config:
                inner_config = config["config"]
            if "class_name" not in config:
                raise ValueError(
                    f"Unknown `config` as a `dict`, config={config}"
                )

            # Check case where config is function or class and in custom objects
            if custom_objects and (
                config["class_name"] in custom_objects
                or config.get("registered_name") in custom_objects
                or (
                    isinstance(inner_config, str)
                    and inner_config in custom_objects
                )
            ):
                has_custom_object = True

            # Case where config is function but not in custom objects
            elif config["class_name"] == "function":
                fn_module_name = config["module"]
                if fn_module_name == "builtins":
                    config = config["config"]
                else:
                    config = config["registered_name"]

            # Case where config is class but not in custom objects
            else:
                if config.get("module", "_") is None:
                    raise TypeError(
                        "Cannot deserialize object of type "
                        f"`{config['class_name']}`. If "
                        f"`{config['class_name']}` is a custom class, please "
                        "register it using the "
                        "`@keras.saving.register_keras_serializable()` "
                        "decorator."
                    )
                config = config["class_name"]

        if not has_custom_object:
            # Return if not found in either module objects or custom objects
            if config not in module_objects:
                # Object has already been deserialized
                return config
            if isinstance(module_objects[config], types.FunctionType):
                return deserialize_keras_object(
                    serialize_with_public_fn(
                        module_objects[config], config, fn_module_name
                    ),
                    custom_objects=custom_objects,
                )
            return deserialize_keras_object(
                serialize_with_public_class(
                    module_objects[config], inner_config=inner_config
                ),
                custom_objects=custom_objects,
            )

    if isinstance(config, PLAIN_TYPES):
        return config
    if not isinstance(config, dict):
        raise TypeError(f"Could not parse config: {config}")

    if "class_name" not in config or "config" not in config:
        return {
            key: deserialize_keras_object(
                value, custom_objects=custom_objects, safe_mode=safe_mode
            )
            for key, value in config.items()
        }

    class_name = config["class_name"]
    inner_config = config["config"] or {}
    custom_objects = custom_objects or {}

    # Special cases:
    if class_name == "__keras_tensor__":
        obj = backend.KerasTensor(
            inner_config["shape"], dtype=inner_config["dtype"]
        )
        obj._pre_serialization_keras_history = inner_config["keras_history"]
        return obj

    if class_name == "__tensor__":
        return backend.convert_to_tensor(
            inner_config["value"], dtype=inner_config["dtype"]
        )
    if class_name == "__numpy__":
        return np.array(inner_config["value"], dtype=inner_config["dtype"])
    if config["class_name"] == "__bytes__":
        return inner_config["value"].encode("utf-8")
    if config["class_name"] == "__ellipsis__":
        return Ellipsis
    if config["class_name"] == "__slice__":
        return slice(
            deserialize_keras_object(
                inner_config["start"],
                custom_objects=custom_objects,
                safe_mode=safe_mode,
            ),
            deserialize_keras_object(
                inner_config["stop"],
                custom_objects=custom_objects,
                safe_mode=safe_mode,
            ),
            deserialize_keras_object(
                inner_config["step"],
                custom_objects=custom_objects,
                safe_mode=safe_mode,
            ),
        )
    if config["class_name"] == "__lambda__":
        if safe_mode:
            raise ValueError(
                "Requested the deserialization of a Python lambda. This "
                "carries a potential risk of arbitrary code execution and thus "
                "it is disallowed by default. If you trust the source of the "
                "artifact, you can override this error by passing "
                "`safe_mode=False` to the loading function, or calling "
                "`keras.config.enable_unsafe_deserialization()."
            )
        return python_utils.func_load(inner_config["value"])
    if tf is not None and config["class_name"] == "__typespec__":
        obj = _retrieve_class_or_fn(
            config["spec_name"],
            config["registered_name"],
            config["module"],
            obj_type="class",
            full_config=config,
            custom_objects=custom_objects,
        )
        # Conversion to TensorShape and DType
        inner_config = map(
            lambda x: (
                tf.TensorShape(x)
                if isinstance(x, list)
                else (getattr(tf, x) if hasattr(tf.dtypes, str(x)) else x)
            ),
            inner_config,
        )
        return obj._deserialize(tuple(inner_config))

    # Below: classes and functions.
    module = config.get("module", None)
    registered_name = config.get("registered_name", class_name)

    if class_name == "function":
        fn_name = inner_config
        return _retrieve_class_or_fn(
            fn_name,
            registered_name,
            module,
            obj_type="function",
            full_config=config,
            custom_objects=custom_objects,
        )

    # Below, handling of all classes.
    # First, is it a shared object?
    if "shared_object_id" in config:
        obj = get_shared_object(config["shared_object_id"])
        if obj is not None:
            return obj

    cls = _retrieve_class_or_fn(
        class_name,
        registered_name,
        module,
        obj_type="class",
        full_config=config,
        custom_objects=custom_objects,
    )

    if isinstance(cls, types.FunctionType):
        return cls
    if not hasattr(cls, "from_config"):
        raise TypeError(
            f"Unable to reconstruct an instance of '{class_name}' because "
            f"the class is missing a `from_config()` method. "
            f"Full object config: {config}"
        )

    # Instantiate the class from its config inside a custom object scope
    # so that we can catch any custom objects that the config refers to.
    custom_obj_scope = object_registration.CustomObjectScope(custom_objects)
    safe_mode_scope = SafeModeScope(safe_mode)
    with custom_obj_scope, safe_mode_scope:
        try:
            instance = cls.from_config(inner_config)
        except TypeError as e:
            raise TypeError(
                f"{cls} could not be deserialized properly. Please"
                " ensure that components that are Python object"
                " instances (layers, models, etc.) returned by"
                " `get_config()` are explicitly deserialized in the"
                " model's `from_config()` method."
                f"\n\nconfig={config}.\n\nException encountered: {e}"
            )
        build_config = config.get("build_config", None)
        if build_config and not instance.built:
            instance.build_from_config(build_config)
            instance.built = True
        compile_config = config.get("compile_config", None)
        if compile_config:
            instance.compile_from_config(compile_config)
            instance.compiled = True

    if "shared_object_id" in config:
        record_object_after_deserialization(
            instance, config["shared_object_id"]
        )
    return instance