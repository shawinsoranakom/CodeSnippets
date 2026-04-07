def SET_NULL(collector, field, sub_objs, using):
    collector.add_field_update(field, None, sub_objs)