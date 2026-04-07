def migration_name_fragment(self):
        return "create_collation_%s" % self.name.lower()