def set_empty(self):
        self.where.add(NothingNode(), AND)
        for query in self.combined_queries:
            query.set_empty()