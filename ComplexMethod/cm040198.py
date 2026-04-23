def _decode_helper(
    obj, deserialize=False, module_objects=None, custom_objects=None
):
    """A decoding helper that is TF-object aware.

    Args:
      obj: A decoded dictionary that may represent an object.
      deserialize: Boolean. When True, deserializes any Keras
        objects found in `obj`. Defaults to `False`.
      module_objects: A dictionary of built-in objects to look the name up in.
        Generally, `module_objects` is provided by midlevel library
        implementers.
      custom_objects: A dictionary of custom objects to look the name up in.
        Generally, `custom_objects` is provided by the end user.

    Returns:
      The decoded object.
    """
    if isinstance(obj, dict) and "class_name" in obj:
        if tf.available:
            if obj["class_name"] == "TensorShape":
                return tf.TensorShape(obj["items"])
            elif obj["class_name"] == "TypeSpec":
                from tensorflow.python.framework import type_spec_registry

                return type_spec_registry.lookup(obj["type_spec"])._deserialize(
                    _decode_helper(obj["serialized"])
                )
            elif obj["class_name"] == "CompositeTensor":
                spec = obj["spec"]
                tensors = []
                for dtype, tensor in obj["tensors"]:
                    tensors.append(
                        tf.constant(tensor, dtype=tf.dtypes.as_dtype(dtype))
                    )
                return tf.nest.pack_sequence_as(
                    _decode_helper(spec), tensors, expand_composites=True
                )

        if obj["class_name"] == "__tuple__":
            return tuple(_decode_helper(i) for i in obj["items"])
        elif obj["class_name"] == "__ellipsis__":
            return Ellipsis
        elif deserialize and "__passive_serialization__" in obj:
            # __passive_serialization__ is added by the JSON encoder when
            # encoding an object that has a `get_config()` method.
            try:
                if (
                    "module" not in obj
                ):  # TODO(nkovela): Add TF SavedModel scope
                    return serialization.deserialize_keras_object(
                        obj,
                        module_objects=module_objects,
                        custom_objects=custom_objects,
                    )
                else:
                    return serialization_lib.deserialize_keras_object(
                        obj,
                        module_objects=module_objects,
                        custom_objects=custom_objects,
                    )
            except ValueError:
                pass
        elif obj["class_name"] == "__bytes__":
            return obj["value"].encode("utf-8")
    return obj