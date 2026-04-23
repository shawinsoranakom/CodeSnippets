def has_limit_one(self):
        return self.high_mark is not None and (self.high_mark - self.low_mark) == 1