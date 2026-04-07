def migration_name_fragment(self):
        if self.old_name:
            return "rename_%s_%s" % (self.old_name_lower, self.new_name_lower)
        return "rename_%s_%s_%s" % (
            self.model_name_lower,
            "_".join(self.old_fields),
            self.new_name_lower,
        )