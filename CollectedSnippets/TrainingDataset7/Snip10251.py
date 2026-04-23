def describe(self):
        return "Rename field %s on %s to %s" % (
            self.old_name,
            self.model_name,
            self.new_name,
        )