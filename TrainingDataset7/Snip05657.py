def is_collapsible(self):
        if any(field in self.fields for field in self.form.errors):
            return False
        return "collapse" in self.classes