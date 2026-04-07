def collect(self, objs, source=None, source_attr=None, **kwargs):
        for obj in objs:
            if source_attr and not source_attr.endswith("+"):
                related_name = source_attr % {
                    "class": source._meta.model_name,
                    "app_label": source._meta.app_label,
                }
                self.add_edge(getattr(obj, related_name), obj)
            else:
                self.add_edge(None, obj)
            self.model_objs[obj._meta.model].add(obj)
        try:
            return super().collect(objs, source_attr=source_attr, **kwargs)
        except models.ProtectedError as e:
            self.protected.update(e.protected_objects)
        except models.RestrictedError as e:
            self.protected.update(e.restricted_objects)