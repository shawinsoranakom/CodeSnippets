def get_parent_list(self):
        """
        Return all the ancestors of this model as a list ordered by MRO.
        Backward compatibility method.
        """
        return list(self.all_parents)