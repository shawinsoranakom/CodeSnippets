def remove_index(self, model, index, concurrently=False):
        self.execute(index.remove_sql(model, self, concurrently=concurrently))