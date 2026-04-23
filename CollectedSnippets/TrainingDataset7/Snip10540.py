def get_constraint_by_name(self, name):
        for constraint in self.options["constraints"]:
            if constraint.name == name:
                return constraint
        raise ValueError("No constraint named %s on model %s" % (name, self.name))