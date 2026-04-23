 def reducer(self, key, values):

        total = sum(values)
        self.handle_budget_notifications(key, total)
        yield key, sum(values)
