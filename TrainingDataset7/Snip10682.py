def get_violation_error_message(self):
        return self.violation_error_message % {"name": self.name}