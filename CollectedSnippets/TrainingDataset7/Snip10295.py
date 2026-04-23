def migration_name_fragment(self):
        return "alter_%s_table" % self.name_lower