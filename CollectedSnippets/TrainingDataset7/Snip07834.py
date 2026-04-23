def migration_name_fragment(self):
        return "%s_validate_%s" % (self.model_name.lower(), self.name.lower())