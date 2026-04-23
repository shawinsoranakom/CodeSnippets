def serialize_keras_object(obj):
    """Retrieve the config dict by serializing the Keras object.

    `serialize_keras_object()` serializes a Keras object to a python dictionary
    that represents the object, and is a reciprocal function of
    `deserialize_keras_object()`. See `deserialize_keras_object()` for more
    information about the config format.

    Args:
        obj: the Keras object to serialize.

    Returns:
        A python dict that represents the object. The python dict can be
        deserialized via `deserialize_keras_object()`.
    """
    if obj is None:
        return obj

    if isinstance(obj, PLAIN_TYPES):
        return obj

    if isinstance(obj, (list, tuple)):
        config_arr = [serialize_keras_object(x) for x in obj]
        return tuple(config_arr) if isinstance(obj, tuple) else config_arr
    if isinstance(obj, dict):
        return serialize_dict(obj)

    # Special cases:
    if isinstance(obj, bytes):
        return {
            "class_name": "__bytes__",
            "config": {"value": obj.decode("utf-8")},
        }
    if isinstance(obj, slice):
        return {
            "class_name": "__slice__",
            "config": {
                "start": serialize_keras_object(obj.start),
                "stop": serialize_keras_object(obj.stop),
                "step": serialize_keras_object(obj.step),
            },
        }
    # Ellipsis is an instance, and ellipsis class is not in global scope.
    # checking equality also fails elsewhere in the library, so we have
    # to dynamically get the type.
    if isinstance(obj, type(Ellipsis)):
        return {"class_name": "__ellipsis__", "config": {}}
    if isinstance(obj, backend.KerasTensor):
        history = getattr(obj, "_keras_history", None)
        if history:
            history = list(history)
            history[0] = history[0].name
        return {
            "class_name": "__keras_tensor__",
            "config": {
                "shape": obj.shape,
                "dtype": obj.dtype,
                "keras_history": history,
            },
        }
    if tf.available and isinstance(obj, tf.TensorShape):
        return obj.as_list() if obj._dims is not None else None
    if backend.is_tensor(obj):
        return {
            "class_name": "__tensor__",
            "config": {
                "value": backend.convert_to_numpy(obj).tolist(),
                "dtype": backend.standardize_dtype(obj.dtype),
            },
        }
    if type(obj).__module__ == np.__name__:
        if isinstance(obj, np.ndarray) and obj.ndim > 0:
            return {
                "class_name": "__numpy__",
                "config": {
                    "value": obj.tolist(),
                    "dtype": backend.standardize_dtype(obj.dtype),
                },
            }
        else:
            # Treat numpy floats / etc as plain types.
            return obj.item()
    if tf.available and isinstance(obj, tf.DType):
        return obj.name
    if isinstance(obj, types.FunctionType) and obj.__name__ == "<lambda>":
        warnings.warn(
            "The object being serialized includes a `lambda`. This is unsafe. "
            "In order to reload the object, you will have to pass "
            "`safe_mode=False` to the loading function. "
            "Please avoid using `lambda` in the "
            "future, and use named Python functions instead. "
            f"This is the `lambda` being serialized: {inspect.getsource(obj)}",
            stacklevel=2,
        )
        return {
            "class_name": "__lambda__",
            "config": {
                "value": python_utils.func_dump(obj),
            },
        }
    if tf.available and isinstance(obj, tf.TypeSpec):
        ts_config = obj._serialize()
        # TensorShape and tf.DType conversion
        ts_config = list(
            map(
                lambda x: (
                    x.as_list()
                    if isinstance(x, tf.TensorShape)
                    else (x.name if isinstance(x, tf.DType) else x)
                ),
                ts_config,
            )
        )
        return {
            "class_name": "__typespec__",
            "spec_name": obj.__class__.__name__,
            "module": obj.__class__.__module__,
            "config": ts_config,
            "registered_name": None,
        }

    inner_config = _get_class_or_fn_config(obj)
    config_with_public_class = serialize_with_public_class(
        obj.__class__, inner_config
    )

    if config_with_public_class is not None:
        get_build_and_compile_config(obj, config_with_public_class)
        record_object_after_serialization(obj, config_with_public_class)
        return config_with_public_class

    # Any custom object or otherwise non-exported object
    if isinstance(obj, types.FunctionType):
        module = obj.__module__
    else:
        module = obj.__class__.__module__
    class_name = obj.__class__.__name__

    if module == "builtins":
        registered_name = None
    else:
        if isinstance(obj, types.FunctionType):
            registered_name = object_registration.get_registered_name(obj)
        else:
            registered_name = object_registration.get_registered_name(
                obj.__class__
            )

    config = {
        "module": module,
        "class_name": class_name,
        "config": inner_config,
        "registered_name": registered_name,
    }
    get_build_and_compile_config(obj, config)
    record_object_after_serialization(obj, config)
    return config