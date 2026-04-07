def is_not_a_generic_foreign_key(f):
            return not (
                f.is_relation
                and f.many_to_one
                and not (hasattr(f.remote_field, "model") and f.remote_field.model)
            )