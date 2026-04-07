def clone(self):
        """Return an exact copy of this ProjectState."""
        new_state = ProjectState(
            models={k: v.clone() for k, v in self.models.items()},
            real_apps=self.real_apps,
        )
        if "apps" in self.__dict__:
            new_state.apps = self.apps.clone()
        new_state.is_delayed = self.is_delayed
        return new_state