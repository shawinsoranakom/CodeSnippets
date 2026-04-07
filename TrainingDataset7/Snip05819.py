def is_registered(self, model):
        """
        Check if a model class is registered with this `AdminSite`.
        """
        return model in self._registry