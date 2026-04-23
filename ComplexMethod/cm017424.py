def _get_defer_select_mask(self, opts, mask, select_mask=None):
        if select_mask is None:
            select_mask = {}
        select_mask[opts.pk] = {}
        # All concrete fields and related objects that are not part of the
        # defer mask must be included. If a relational field is encountered it
        # gets added to the mask for it be considered if `select_related` and
        # the cycle continues by recursively calling this function.
        for field in opts.concrete_fields + opts.related_objects:
            field_mask = mask.pop(field.name, None)
            field_att_mask = None
            if field_attname := getattr(field, "attname", None):
                field_att_mask = mask.pop(field_attname, None)
            if field_mask is None and field_att_mask is None:
                select_mask.setdefault(field, {})
            elif field_mask:
                if not field.is_relation:
                    raise FieldError(next(iter(field_mask)))
                # Virtual fields such as many-to-many and generic foreign keys
                # cannot be effectively deferred. Historically, they were
                # allowed to be passed to QuerySet.defer(). Ignore such field
                # references until a layer of validation at mask alteration
                # time is eventually implemented.
                if field.many_to_many:
                    continue
                field_select_mask = select_mask.setdefault(field, {})
                related_model = field.related_model._meta.concrete_model
                self._get_defer_select_mask(
                    related_model._meta, field_mask, field_select_mask
                )
        # Remaining defer entries must be references to filtered relations
        # otherwise they are surfaced as missing field errors.
        for field_name, field_mask in mask.items():
            if filtered_relation := self._filtered_relations.get(field_name):
                relation = opts.get_field(filtered_relation.relation_name)
                field_select_mask = select_mask.setdefault((field_name, relation), {})
                related_model = relation.related_model._meta.concrete_model
                self._get_defer_select_mask(
                    related_model._meta, field_mask, field_select_mask
                )
            else:
                opts.get_field(field_name)
        return select_mask