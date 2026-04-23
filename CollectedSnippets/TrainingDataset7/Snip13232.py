def pop(self):
        if len(self.dicts) == 1:
            raise ContextPopException
        return self.dicts.pop()