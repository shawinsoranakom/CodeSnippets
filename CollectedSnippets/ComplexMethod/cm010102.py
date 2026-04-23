def _get_named_tuple_properties(
    obj,
    loc: torch._C._jit_tree_views.SourceRange | None = None,
    rcb=None,
):
    if loc is None:
        loc = fake_range()

    if not issubclass(obj, tuple) or not hasattr(obj, "_fields"):
        raise AssertionError(
            f"expected namedtuple (tuple subclass with _fields), got {obj}"
        )
    if hasattr(obj, "_field_defaults"):
        defaults = [
            obj._field_defaults[field]
            for field in obj._fields
            if field in obj._field_defaults
        ]
    else:
        defaults = []

    obj_annotations = inspect.get_annotations(obj)
    if len(obj_annotations) == 0 and hasattr(obj, "__base__"):
        obj_annotations = inspect.get_annotations(
            # pyrefly: ignore [bad-argument-type]
            obj.__base__
        )

    annotations = []
    for field in obj._fields:
        if field in obj_annotations:
            field_type = obj_annotations[field]
            # [Note: ForwardRef annotations in NamedTuple attributes]
            # NamedTuple types are slightly different from normal types.
            #
            # Normally, annotations are evaluated like this (during jit.script):
            # 1. Load strings of python code into c++ and parse.
            # 2. Get annotations as strings
            # 3. Use the PythonResolver's resolution callback (rcb) to convert
            #    the string into a python object
            # 4. We call into annotations.py:ann_to_type to convert python obj
            #    from step 3 into a type that torchscript understands.
            #
            # NamedTuples are more complicated, because it has sub-types.
            # Normally, once we have the NamedTuple type object from #3,
            # we can just look at the annotation literal values and use
            # ann_to_type directly on them.
            #
            # But sometimes, users will annotate with string literals, e.g.
            #    x: 'int'
            # This also happens with PEP563 (from __forward__ import annotations)
            #
            # These annotations appear in the annotation dict as ForwardRef('int').
            #
            # Then, we need to convert the string into a python object. This
            # requires having local context for custom objects or imported types.
            # rcb() is what gives us this. So, we plumb rcb through the stack so
            # it can be used in this context for the if block below.
            #
            # FAQ:
            # - Why do we need this special handling for NamedTuple but string
            #   annotations work fine for normal types? Normally, we parse the
            #   string directly and then call rcb() directly from C++.
            # - Why not use ForwardRef._evaluate? For that, we need globals()
            #   and locals() for the local context where the NamedTuple was defined.
            #   rcb is what lets us look up into these. So, basically rcb does the
            #   hard work for us.
            if isinstance(field_type, ForwardRef) and rcb is not None:
                rcb_type = rcb(field_type.__forward_arg__)
                # rcb returns None if it can't find anything.
                if rcb_type is None:
                    raise ValueError(
                        f"Unknown type annotation: '{field_type}' in NamedTuple {obj.__name__}."
                        f" Likely due to partial support for ForwardRef parameters in NamedTuples, see #95858."
                        f" Issue occurred at {loc.highlight()}"
                    )
                field_type = rcb_type
            the_type = torch.jit.annotations.ann_to_type(field_type, loc, rcb)
            annotations.append(the_type)
        else:
            annotations.append(torch._C.TensorType.getInferred())
    return type(obj).__name__, obj._fields, annotations, defaults