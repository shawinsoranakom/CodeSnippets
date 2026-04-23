def set_formatter_from_type(self):
        if self.type and not self.formatter:
            self.formatter = self.validate_formatter(self.type)
        if self.formatter in {"boolean", "bool"}:
            valid_trues = ["True", "true", "1", "yes"]
            valid_falses = ["False", "false", "0", "no"]
            if self.default in valid_trues:
                self.default = True
            if self.default in valid_falses:
                self.default = False
        elif self.formatter in {"integer", "int"}:
            self.default = int(self.default)
        elif self.formatter in {"float"}:
            self.default = float(self.default)
        else:
            self.default = str(self.default)
        return self