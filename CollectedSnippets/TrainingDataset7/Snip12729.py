def get_context(self):
        return {
            "errors": self,
            "error_class": self.error_class,
        }