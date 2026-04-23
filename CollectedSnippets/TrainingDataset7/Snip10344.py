def migration_name_fragment(self):
        return "%s_%s" % (self.model_name_lower, self.index.name.lower())