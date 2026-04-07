def captured_queries(self):
        return self.connection.queries[self.initial_queries : self.final_queries]