def SET(value):
    if callable(value):

        def set_on_delete(collector, field, sub_objs, using):
            collector.add_field_update(field, value(), sub_objs)

    else:

        def set_on_delete(collector, field, sub_objs, using):
            collector.add_field_update(field, value, sub_objs)

        set_on_delete.lazy_sub_objs = True

    set_on_delete.deconstruct = lambda: ("django.db.models.SET", (value,), {})
    return set_on_delete