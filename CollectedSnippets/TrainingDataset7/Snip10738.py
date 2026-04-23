def set_on_delete(collector, field, sub_objs, using):
            collector.add_field_update(field, value(), sub_objs)