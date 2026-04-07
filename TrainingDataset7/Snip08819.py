def log_output(self):
        return self.stderr if self.scriptable else self.stdout