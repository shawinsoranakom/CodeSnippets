def migration_name_fragment(self):
        return "alter_%s_%s" % (self.name_lower, self.option_name)