def is_data_field(f):
            return isinstance(f, Field) and not f.many_to_many