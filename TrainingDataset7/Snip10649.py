def get_constraints(self):
        constraints = [(self.__class__, self._meta.constraints)]
        for parent_class in self._meta.all_parents:
            if parent_class._meta.constraints:
                constraints.append((parent_class, parent_class._meta.constraints))
        return constraints