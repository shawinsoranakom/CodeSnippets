def add_condition(self, condition, reason):
        return self.__class__(*self.conditions, (condition, reason))