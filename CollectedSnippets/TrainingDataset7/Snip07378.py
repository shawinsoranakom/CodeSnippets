def count(self, val):
        "Standard list count method"
        count = 0
        for i in self:
            if val == i:
                count += 1
        return count