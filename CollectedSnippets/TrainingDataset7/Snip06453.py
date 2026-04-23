def related_manager_cls(self):
        return create_generic_related_manager(
            self.rel.model._default_manager.__class__,
            self.rel,
        )