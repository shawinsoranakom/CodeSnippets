def __new__(cls, name, bases, ns, total=True, closed=None,
                extra_items=NoExtraItems):
        """Create a new typed dict class object.

        This method is called when TypedDict is subclassed,
        or when TypedDict is instantiated. This way
        TypedDict supports all three syntax forms described in its docstring.
        Subclasses and instances of TypedDict return actual dictionaries.
        """
        for base in bases:
            if type(base) is not _TypedDictMeta and base is not Generic:
                raise TypeError('cannot inherit from both a TypedDict type '
                                'and a non-TypedDict base class')
        if closed is not None and extra_items is not NoExtraItems:
            raise TypeError(f"Cannot combine closed={closed!r} and extra_items")

        if any(issubclass(b, Generic) for b in bases):
            generic_base = (Generic,)
        else:
            generic_base = ()

        ns_annotations = ns.pop('__annotations__', None)

        tp_dict = type.__new__(_TypedDictMeta, name, (*generic_base, dict), ns)

        if not hasattr(tp_dict, '__orig_bases__'):
            tp_dict.__orig_bases__ = bases

        if ns_annotations is not None:
            own_annotate = None
            own_annotations = ns_annotations
        elif (own_annotate := _lazy_annotationlib.get_annotate_from_class_namespace(ns)) is not None:
            own_annotations = _lazy_annotationlib.call_annotate_function(
                own_annotate, _lazy_annotationlib.Format.FORWARDREF, owner=tp_dict
            )
        else:
            own_annotate = None
            own_annotations = {}
        msg = "TypedDict('Name', {f0: t0, f1: t1, ...}); each t must be a type"
        own_checked_annotations = {
            n: _type_check(tp, msg, owner=tp_dict, module=tp_dict.__module__)
            for n, tp in own_annotations.items()
        }
        required_keys = set()
        optional_keys = set()
        readonly_keys = set()
        mutable_keys = set()

        for base in bases:
            base_required = base.__dict__.get('__required_keys__', set())
            required_keys |= base_required
            optional_keys -= base_required

            base_optional = base.__dict__.get('__optional_keys__', set())
            required_keys -= base_optional
            optional_keys |= base_optional

            readonly_keys.update(base.__dict__.get('__readonly_keys__', ()))
            mutable_keys.update(base.__dict__.get('__mutable_keys__', ()))

        for annotation_key, annotation_type in own_checked_annotations.items():
            qualifiers = set(_get_typeddict_qualifiers(annotation_type))
            if Required in qualifiers:
                is_required = True
            elif NotRequired in qualifiers:
                is_required = False
            else:
                is_required = total

            if is_required:
                required_keys.add(annotation_key)
                optional_keys.discard(annotation_key)
            else:
                optional_keys.add(annotation_key)
                required_keys.discard(annotation_key)

            if ReadOnly in qualifiers:
                if annotation_key in mutable_keys:
                    raise TypeError(
                        f"Cannot override mutable key {annotation_key!r}"
                        " with read-only key"
                    )
                readonly_keys.add(annotation_key)
            else:
                mutable_keys.add(annotation_key)
                readonly_keys.discard(annotation_key)

        assert required_keys.isdisjoint(optional_keys), (
            f"Required keys overlap with optional keys in {name}:"
            f" {required_keys=}, {optional_keys=}"
        )

        def __annotate__(format):
            annos = {}
            for base in bases:
                if base is Generic:
                    continue
                base_annotate = base.__annotate__
                if base_annotate is None:
                    continue
                base_annos = _lazy_annotationlib.call_annotate_function(
                    base_annotate, format, owner=base)
                annos.update(base_annos)
            if own_annotate is not None:
                own = _lazy_annotationlib.call_annotate_function(
                    own_annotate, format, owner=tp_dict)
                if format != _lazy_annotationlib.Format.STRING:
                    own = {
                        n: _type_check(tp, msg, module=tp_dict.__module__)
                        for n, tp in own.items()
                    }
            elif format == _lazy_annotationlib.Format.STRING:
                own = _lazy_annotationlib.annotations_to_string(own_annotations)
            elif format in (_lazy_annotationlib.Format.FORWARDREF, _lazy_annotationlib.Format.VALUE):
                own = own_checked_annotations
            else:
                raise NotImplementedError(format)
            annos.update(own)
            return annos

        tp_dict.__annotate__ = __annotate__
        tp_dict.__required_keys__ = frozenset(required_keys)
        tp_dict.__optional_keys__ = frozenset(optional_keys)
        tp_dict.__readonly_keys__ = frozenset(readonly_keys)
        tp_dict.__mutable_keys__ = frozenset(mutable_keys)
        tp_dict.__total__ = total
        tp_dict.__closed__ = closed
        tp_dict.__extra_items__ = extra_items
        return tp_dict