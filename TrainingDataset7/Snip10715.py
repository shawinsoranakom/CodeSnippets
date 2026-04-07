def SET_DEFAULT(collector, field, sub_objs, using):
    collector.add_field_update(field, field.get_default(), sub_objs)