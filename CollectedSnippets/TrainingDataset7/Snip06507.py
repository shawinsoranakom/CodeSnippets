def get_all_objects_for_this_type(self, **kwargs):
        """
        Return all objects of this type for the keyword arguments given.
        """
        return self.model_class()._base_manager.filter(**kwargs)