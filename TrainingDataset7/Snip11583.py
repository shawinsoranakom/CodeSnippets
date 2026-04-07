def get_normalized_value(value, lhs):
    from django.db.models import Model

    if isinstance(value, Model):
        if not value._is_pk_set():
            raise ValueError("Model instances passed to related filters must be saved.")
        value_list = []
        sources = composite.unnest(lhs.output_field.path_infos[-1].target_fields)
        for source in sources:
            while not isinstance(value, source.model) and source.remote_field:
                source = source.remote_field.model._meta.get_field(
                    source.remote_field.field_name
                )
            try:
                value_list.append(getattr(value, source.attname))
            except AttributeError:
                # A case like
                # Restaurant.objects.filter(place=restaurant_instance), where
                # place is a OneToOneField and the primary key of Restaurant.
                pk = value.pk
                return pk if isinstance(pk, tuple) else (pk,)
        return tuple(value_list)
    if not isinstance(value, tuple):
        return (value,)
    return value