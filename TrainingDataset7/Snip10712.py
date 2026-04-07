def RESTRICT(collector, field, sub_objs, using):
    collector.add_restricted_objects(field, sub_objs)
    collector.add_dependency(field.remote_field.model, field.model)