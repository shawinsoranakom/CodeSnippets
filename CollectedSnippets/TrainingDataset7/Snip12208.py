def clone(self, using):
        return RawQuery(self.sql, using, params=self.params)