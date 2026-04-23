def natural_key(self):
        return (self.app_label, self.model)