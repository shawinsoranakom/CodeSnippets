def describe(self):
        return "Concurrently create index %s on field(s) %s of model %s" % (
            self.index.name,
            ", ".join(self.index.fields),
            self.model_name,
        )