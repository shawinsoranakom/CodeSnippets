def migration_name_fragment(self):
        return "alter_%s_%s" % (self.model_name_lower, self.name_lower)