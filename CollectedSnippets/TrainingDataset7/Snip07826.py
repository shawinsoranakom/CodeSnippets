def describe(self):
        return "Create not valid constraint %s on model %s" % (
            self.constraint.name,
            self.model_name,
        )