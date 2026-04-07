def _reset_dicts(self, value=None):
        builtins = {"True": True, "False": False, "None": None}
        self.dicts = [builtins]
        if isinstance(value, BaseContext):
            self.dicts += value.dicts[1:]
        elif value is not None:
            self.dicts.append(value)