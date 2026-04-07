def clear_restricted_objects_from_queryset(self, model, qs):
        if model in self.restricted_objects:
            objs = set(
                qs.filter(
                    pk__in=[
                        obj.pk
                        for objs in self.restricted_objects[model].values()
                        for obj in objs
                    ]
                )
            )
            self.clear_restricted_objects_from_set(model, objs)