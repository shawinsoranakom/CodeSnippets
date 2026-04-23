def describe(self):
        return "Create constraint %s on model %s" % (
            self.constraint.name,
            self.model_name,
        )