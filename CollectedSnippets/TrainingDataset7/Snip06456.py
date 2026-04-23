def __call__(self, *, manager):
            manager = getattr(self.model, manager)
            manager_class = create_generic_related_manager(manager.__class__, rel)
            return manager_class(instance=self.instance)