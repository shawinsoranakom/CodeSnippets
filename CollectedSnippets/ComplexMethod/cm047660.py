def get_cache_size(
        obj,
        *,
        cache_info: str = '',
        seen_ids: set[int] | None = None,
        class_slots: dict[type, Iterable[str]] | None = None
    ) -> int:
    """ A non-thread-safe recursive object size estimator """
    from odoo.models import BaseModel  # noqa: PLC0415
    from odoo.api import Environment  # noqa: PLC0415

    if seen_ids is None:
        # count internal constants as 0 bytes
        seen_ids = set(map(id, (None, False, True)))
    if class_slots is None:
        class_slots = {}  # {class_id: combined_slots}
    total_size = 0
    objects = [obj]

    while objects:
        cur_obj = objects.pop()
        if id(cur_obj) in seen_ids:
            continue

        if cache_info and isinstance(cur_obj, (BaseModel, Environment)):
            _logger.error('%s is cached by %s', cur_obj, cache_info)
            continue

        seen_ids.add(id(cur_obj))
        total_size += sys.getsizeof(cur_obj)

        if hasattr(cur_obj, '__slots__'):
            cur_obj_cls = type(cur_obj)
            attributes = class_slots.get(id(cur_obj_cls))
            if attributes is None:
                class_slots[id(cur_obj_cls)] = attributes = tuple({
                    f'_{cls.__name__}{attr}' if attr.startswith('__') else attr
                    for cls in cur_obj_cls.mro()
                    for attr in getattr(cls, '__slots__', ())
                })
            objects.extend(getattr(cur_obj, attr, None) for attr in attributes)
        if hasattr(cur_obj, '__dict__'):
            objects.append(object.__dict__)

        if isinstance(cur_obj, Mapping):
            objects.extend(cur_obj.values())
            objects.extend(cur_obj.keys())
        elif isinstance(cur_obj, Collection) and not isinstance(cur_obj, (str, bytes, bytearray)):
            objects.extend(cur_obj)

    return total_size