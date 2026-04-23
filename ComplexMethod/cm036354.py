def assumes(obj, attr, is_callable=False, is_instance_of=None):
    import inspect
    from dataclasses import is_dataclass

    assumption_msg = (
        f"LMCache connector currently assumes that {obj} has a(n) {attr} attribute"
    )
    if hasattr(obj, attr):
        attr_value = getattr(obj, attr)
    elif is_dataclass(obj) and attr in getattr(obj, "__dataclass_fields__", {}):
        field = obj.__dataclass_fields__[attr]
        field_type = field.type
        origin = getattr(field_type, "__origin__", None)
        if origin is not None:
            field_type = origin
        attr_value = field_type
    else:
        raise AssertionError(assumption_msg)
    if is_callable:
        assumption_msg += f" and that {obj}.{attr} is a callable"
        assert callable(attr_value), assumption_msg
    if is_instance_of:
        assumption_msg += f" and that {obj}.{attr} is an instance of {is_instance_of}"
        if isinstance(attr_value, property):
            fget = attr_value.fget
            assert fget is not None, f"Property {obj}.{attr} has no fget"
            sig = inspect.signature(fget)
            ret_anno = sig.return_annotation
            assert ret_anno is not inspect._empty, (
                f"Property {obj}.{attr} has no return annotation"
            )
            assert ret_anno == is_instance_of, assumption_msg
        else:
            if isinstance(attr_value, type):
                assert attr_value is is_instance_of, assumption_msg
            else:
                assert isinstance(attr_value, is_instance_of), assumption_msg