def __eq__(self, other):
            if self.eq_calls > 0:
                return True
            self.eq_calls += 1
            return False