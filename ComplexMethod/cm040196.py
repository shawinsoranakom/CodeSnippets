def class_and_config_for_serialized_keras_object(
    config,
    module_objects=None,
    custom_objects=None,
    printable_module_name="object",
):
    """Returns the class name and config for a serialized keras object."""

    if (
        not isinstance(config, dict)
        or "class_name" not in config
        or "config" not in config
    ):
        raise ValueError(
            f"Improper config format for {config}. "
            "Expecting python dict contains `class_name` and `config` as keys"
        )

    class_name = config["class_name"]
    cls = object_registration.get_registered_object(
        class_name, custom_objects, module_objects
    )
    if cls is None:
        raise ValueError(
            f"Unknown {printable_module_name}: '{class_name}'. "
            "Please ensure you are using a `keras.utils.custom_object_scope` "
            "and that this object is included in the scope. See "
            "https://www.tensorflow.org/guide/keras/save_and_serialize"
            "#registering_the_custom_object for details."
        )

    cls_config = config["config"]
    # Check if `cls_config` is a list. If it is a list, return the class and the
    # associated class configs for recursively deserialization. This case will
    # happen on the old version of sequential model (e.g. `keras_version` ==
    # "2.0.6"), which is serialized in a different structure, for example
    # "{'class_name': 'Sequential',
    #   'config': [{'class_name': 'Embedding', 'config': ...}, {}, ...]}".
    if isinstance(cls_config, list):
        return (cls, cls_config)

    deserialized_objects = {}
    for key, item in cls_config.items():
        if key == "name":
            # Assume that the value of 'name' is a string that should not be
            # deserialized as a function. This avoids the corner case where
            # cls_config['name'] has an identical name to a custom function and
            # gets converted into that function.
            deserialized_objects[key] = item
        elif isinstance(item, dict) and "__passive_serialization__" in item:
            deserialized_objects[key] = deserialize_keras_object(
                item,
                module_objects=module_objects,
                custom_objects=custom_objects,
                printable_module_name="config_item",
            )
        # Also consider looking up functions in `module_objects`.
        elif isinstance(item, str) and inspect.isfunction(
            object_registration.get_registered_object(
                item, custom_objects, module_objects
            )
        ):
            # Handle custom functions here. When saving functions, we only save
            # the function's name as a string. If we find a matching string in
            # the custom objects during deserialization, we convert the string
            # back to the original function.
            # Note that a potential issue is that a string field could have a
            # naming conflict with a custom function name, but this should be a
            # rare case.  This issue does not occur if a string field has a
            # naming conflict with a custom object, since the config of an
            # object will always be a dict.
            deserialized_objects[key] = (
                object_registration.get_registered_object(
                    item, custom_objects, module_objects
                )
            )
    for key, item in deserialized_objects.items():
        cls_config[key] = deserialized_objects[key]

    return (cls, cls_config)