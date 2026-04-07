def is_self_referential(f):
            return f.is_relation and f.remote_field.model is model