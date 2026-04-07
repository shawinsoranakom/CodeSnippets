def related_manager_cls(self):
        related_model = self.rel.related_model

        return create_reverse_many_to_one_manager(
            related_model._default_manager.__class__,
            self.rel,
        )