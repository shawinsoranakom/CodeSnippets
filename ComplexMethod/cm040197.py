def deserialize_keras_object(
    identifier,
    module_objects=None,
    custom_objects=None,
    printable_module_name="object",
):
    """Turns the serialized form of a Keras object back into an actual object.

    This function is for mid-level library implementers rather than end users.

    Importantly, this utility requires you to provide the dict of
    `module_objects` to use for looking up the object config; this is not
    populated by default. If you need a deserialization utility that has
    preexisting knowledge of built-in Keras objects, use e.g.
    `keras.layers.deserialize(config)`, `keras.metrics.deserialize(config)`,
    etc.

    Calling `deserialize_keras_object` while underneath the
    `SharedObjectLoadingScope` context manager will cause any already-seen
    shared objects to be returned as-is rather than creating a new object.

    Args:
      identifier: the serialized form of the object.
      module_objects: A dictionary of built-in objects to look the name up in.
        Generally, `module_objects` is provided by midlevel library
        implementers.
      custom_objects: A dictionary of custom objects to look the name up in.
        Generally, `custom_objects` is provided by the end user.
      printable_module_name: A human-readable string representing the type of
        the object. Printed in case of exception.

    Returns:
      The deserialized object.

    Example:

    A mid-level library implementer might want to implement a utility for
    retrieving an object from its config, as such:

    ```python
    def deserialize(config, custom_objects=None):
       return deserialize_keras_object(
         identifier,
         module_objects=globals(),
         custom_objects=custom_objects,
         name="MyObjectType",
       )
    ```

    This is how e.g. `keras.layers.deserialize()` is implemented.
    """

    if identifier is None:
        return None

    if isinstance(identifier, dict):
        # In this case we are dealing with a Keras config dictionary.
        config = identifier
        (cls, cls_config) = class_and_config_for_serialized_keras_object(
            config, module_objects, custom_objects, printable_module_name
        )

        # If this object has already been loaded (i.e. it's shared between
        # multiple objects), return the already-loaded object.
        shared_object_id = config.get(SHARED_OBJECT_KEY)
        shared_object = _shared_object_loading_scope().get(shared_object_id)
        if shared_object is not None:
            return shared_object

        if hasattr(cls, "from_config"):
            arg_spec = inspect.getfullargspec(cls.from_config)
            custom_objects = custom_objects or {}

            if "custom_objects" in arg_spec.args:
                deserialized_obj = cls.from_config(
                    cls_config,
                    custom_objects={
                        **object_registration.GLOBAL_CUSTOM_OBJECTS,
                        **custom_objects,
                    },
                )
            else:
                with object_registration.CustomObjectScope(custom_objects):
                    deserialized_obj = cls.from_config(cls_config)
        else:
            # Then `cls` may be a function returning a class.
            # in this case by convention `config` holds
            # the kwargs of the function.
            custom_objects = custom_objects or {}
            with object_registration.CustomObjectScope(custom_objects):
                deserialized_obj = cls(**cls_config)

        # Add object to shared objects, in case we find it referenced again.
        _shared_object_loading_scope().set(shared_object_id, deserialized_obj)

        return deserialized_obj

    elif isinstance(identifier, str):
        object_name = identifier
        if custom_objects and object_name in custom_objects:
            obj = custom_objects.get(object_name)
        elif (
            object_name
            in object_registration._THREAD_LOCAL_CUSTOM_OBJECTS.__dict__
        ):
            obj = object_registration._THREAD_LOCAL_CUSTOM_OBJECTS.__dict__[
                object_name
            ]
        elif object_name in object_registration._GLOBAL_CUSTOM_OBJECTS:
            obj = object_registration._GLOBAL_CUSTOM_OBJECTS[object_name]
        else:
            obj = module_objects.get(object_name)
            if obj is None:
                raise ValueError(
                    f"Unknown {printable_module_name}: '{object_name}'. "
                    "Please ensure you are using a "
                    "`keras.utils.custom_object_scope` "
                    "and that this object is included in the scope. See "
                    "https://www.tensorflow.org/guide/keras/save_and_serialize"
                    "#registering_the_custom_object for details."
                )

        # Classes passed by name are instantiated with no args, functions are
        # returned as-is.
        if inspect.isclass(obj):
            return obj()
        return obj
    elif inspect.isfunction(identifier):
        # If a function has already been deserialized, return as is.
        return identifier
    else:
        raise ValueError(
            "Could not interpret serialized "
            f"{printable_module_name}: {identifier}"
        )