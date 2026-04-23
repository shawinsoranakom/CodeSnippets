def is_collapsible(self):
        if any(self.formset.errors):
            return False
        return "collapse" in self.classes