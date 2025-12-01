 def reducer(self, key, values):

        yield key, sum(values)
