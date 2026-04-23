def _proto_hook(cls, other):
    if not cls.__dict__.get('_is_protocol', False):
        return NotImplemented

    for attr in cls.__protocol_attrs__:
        for base in other.__mro__:
            # Check if the members appears in the class dictionary...
            if attr in base.__dict__:
                if base.__dict__[attr] is None:
                    return NotImplemented
                break

            # ...or in annotations, if it is a sub-protocol.
            if issubclass(other, Generic) and getattr(other, "_is_protocol", False):
                # We avoid the slower path through annotationlib here because in most
                # cases it should be unnecessary.
                try:
                    annos = base.__annotations__
                except Exception:
                    annos = _lazy_annotationlib.get_annotations(
                        base, format=_lazy_annotationlib.Format.FORWARDREF
                    )
                if attr in annos:
                    break
        else:
            return NotImplemented
    return True