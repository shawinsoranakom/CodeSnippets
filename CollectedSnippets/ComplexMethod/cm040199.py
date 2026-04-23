def get_json_type(obj):
    """Serializes any object to a JSON-serializable structure.

    Args:
        obj: the object to serialize

    Returns:
        JSON-serializable structure representing `obj`.

    Raises:
        TypeError: if `obj` cannot be serialized.
    """
    # if obj is a serializable Keras class instance
    # e.g. optimizer, layer
    if hasattr(obj, "get_config"):
        # TODO(nkovela): Replace with legacy serialization
        serialized = serialization.serialize_keras_object(obj)
        serialized["__passive_serialization__"] = True
        return serialized

    # if obj is any numpy type
    if type(obj).__module__ == np.__name__:
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj.item()

    # misc functions (e.g. loss function)
    if callable(obj):
        return obj.__name__

    # if obj is a python 'type'
    if type(obj).__name__ == type.__name__:
        return obj.__name__

    if tf.available and isinstance(obj, tf.compat.v1.Dimension):
        return obj.value

    if tf.available and isinstance(obj, tf.TensorShape):
        return obj.as_list()

    if tf.available and isinstance(obj, tf.DType):
        return obj.name

    if isinstance(obj, collections.abc.Mapping):
        return dict(obj)

    if obj is Ellipsis:
        return {"class_name": "__ellipsis__"}

    # if isinstance(obj, wrapt.ObjectProxy):
    #     return obj.__wrapped__

    if tf.available and isinstance(obj, tf.TypeSpec):
        from tensorflow.python.framework import type_spec_registry

        try:
            type_spec_name = type_spec_registry.get_name(type(obj))
            return {
                "class_name": "TypeSpec",
                "type_spec": type_spec_name,
                "serialized": obj._serialize(),
            }
        except ValueError:
            raise ValueError(
                f"Unable to serialize {obj} to JSON, because the TypeSpec "
                f"class {type(obj)} has not been registered."
            )
    if tf.available and isinstance(obj, tf.__internal__.CompositeTensor):
        spec = tf.type_spec_from_value(obj)
        tensors = []
        for tensor in tf.nest.flatten(obj, expand_composites=True):
            tensors.append((tensor.dtype.name, tensor.numpy().tolist()))
        return {
            "class_name": "CompositeTensor",
            "spec": get_json_type(spec),
            "tensors": tensors,
        }

    if isinstance(obj, enum.Enum):
        return obj.value

    if isinstance(obj, bytes):
        return {"class_name": "__bytes__", "value": obj.decode("utf-8")}

    raise TypeError(
        f"Unable to serialize {obj} to JSON. Unrecognized type {type(obj)}."
    )