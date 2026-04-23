def migration_name_fragment(self):
        return "rename_%s_%s" % (self.old_name_lower, self.new_name_lower)