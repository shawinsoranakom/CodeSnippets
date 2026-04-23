def allowed_default(self):
        return self.default.allowed_default and all(
            case_.allowed_default for case_ in self.cases
        )