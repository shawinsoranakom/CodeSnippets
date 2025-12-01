 def steps(self):
        return [
            self.mr(mapper=self.mapper,
                    reducer=self.reducer)
        ]
