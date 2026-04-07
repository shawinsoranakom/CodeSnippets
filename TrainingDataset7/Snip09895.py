def add_index(self, model, index, concurrently=False):
        self.execute(
            index.create_sql(model, self, concurrently=concurrently), params=None
        )