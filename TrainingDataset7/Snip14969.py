def get_context_object_name(self, object_list):
        """Get the name of the item to be used in the context."""
        if self.context_object_name:
            return self.context_object_name
        elif hasattr(object_list, "model"):
            return "%s_list" % object_list.model._meta.model_name
        else:
            return None