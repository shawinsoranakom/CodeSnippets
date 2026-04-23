def __call__(self, *, manager):
            manager = getattr(self.model, manager)
            manager_class = create_forward_many_to_many_manager(
                manager.__class__, rel, reverse
            )
            return manager_class(instance=self.instance)