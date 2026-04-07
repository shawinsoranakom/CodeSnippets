def get_exclusion(self):
        if self.exclusion is None:
            return ""
        return f" EXCLUDE {self.exclusion.value}"