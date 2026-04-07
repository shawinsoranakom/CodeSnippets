def related_objects(self, related_model, related_fields, objs):
        qs = super().related_objects(related_model, related_fields, objs)
        return qs.select_related(
            *[related_field.name for related_field in related_fields]
        )