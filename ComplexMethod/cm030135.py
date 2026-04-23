def __new__(cls, typename, bases, ns):
        assert _NamedTuple in bases
        if "__classcell__" in ns:
            raise TypeError(
                "uses of super() and __class__ are unsupported in methods of NamedTuple subclasses")
        for base in bases:
            if base is not _NamedTuple and base is not Generic:
                raise TypeError(
                    'can only inherit from a NamedTuple type and Generic')
        bases = tuple(tuple if base is _NamedTuple else base for base in bases)
        if "__annotations__" in ns:
            types = ns["__annotations__"]
            field_names = list(types)
            annotate = _make_eager_annotate(types)
        elif (original_annotate := _lazy_annotationlib.get_annotate_from_class_namespace(ns)) is not None:
            types = _lazy_annotationlib.call_annotate_function(
                original_annotate, _lazy_annotationlib.Format.FORWARDREF)
            field_names = list(types)

            # For backward compatibility, type-check all the types at creation time
            for typ in types.values():
                _type_check(typ, "field annotation must be a type")

            def annotate(format):
                annos = _lazy_annotationlib.call_annotate_function(
                    original_annotate, format)
                if format != _lazy_annotationlib.Format.STRING:
                    return {key: _type_check(val, f"field {key} annotation must be a type")
                            for key, val in annos.items()}
                return annos
        else:
            # Empty NamedTuple
            field_names = []
            annotate = lambda format: {}
        default_names = []
        for field_name in field_names:
            if field_name in ns:
                default_names.append(field_name)
            elif default_names:
                raise TypeError(f"Non-default namedtuple field {field_name} "
                                f"cannot follow default field"
                                f"{'s' if len(default_names) > 1 else ''} "
                                f"{', '.join(default_names)}")
        nm_tpl = _make_nmtuple(typename, field_names, annotate,
                               defaults=[ns[n] for n in default_names],
                               module=ns['__module__'])
        nm_tpl.__bases__ = bases
        if Generic in bases:
            class_getitem = _generic_class_getitem
            nm_tpl.__class_getitem__ = classmethod(class_getitem)
        # update from user namespace without overriding special namedtuple attributes
        for key, val in ns.items():
            if key in _prohibited:
                raise AttributeError("Cannot overwrite NamedTuple attribute " + key)
            elif key not in _special:
                if key not in nm_tpl._fields:
                    setattr(nm_tpl, key, val)
                try:
                    set_name = type(val).__set_name__
                except AttributeError:
                    pass
                else:
                    try:
                        set_name(val, nm_tpl, key)
                    except BaseException as e:
                        e.add_note(
                            f"Error calling __set_name__ on {type(val).__name__!r} "
                            f"instance {key!r} in {typename!r}"
                        )
                        raise

        if Generic in bases:
            nm_tpl.__init_subclass__()
        return nm_tpl