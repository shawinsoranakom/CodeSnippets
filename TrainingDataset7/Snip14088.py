def check(self):
        warnings = self._check_pattern_name()
        warnings.extend(self.pattern.check())
        warnings.extend(self._check_callback())
        return warnings