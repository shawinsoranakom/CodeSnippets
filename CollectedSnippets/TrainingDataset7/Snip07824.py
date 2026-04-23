def migration_name_fragment(self):
        return "remove_collation_%s" % self.name.lower()