def get_instance_value_for_fields(instance, fields):
        ret = []
        opts = instance._meta
        for field in fields:
            # Gotcha: in some cases (like fixture loading) a model can have
            # different values in parent_ptr_id and parent's id. So, use
            # instance.pk (that is, parent_ptr_id) when asked for instance.id.
            if field.primary_key:
                possible_parent_link = opts.get_ancestor_link(field.model)
                if (
                    not possible_parent_link
                    or possible_parent_link.primary_key
                    or possible_parent_link.model._meta.abstract
                ):
                    ret.append(instance.pk)
                    continue
            ret.append(getattr(instance, field.attname))
        return tuple(ret)