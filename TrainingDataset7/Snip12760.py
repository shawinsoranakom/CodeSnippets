def is_hidden(self):
        return self.input_type == "hidden" if hasattr(self, "input_type") else False