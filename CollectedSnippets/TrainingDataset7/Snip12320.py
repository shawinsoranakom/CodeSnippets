def update_batch(self, pk_list, values, using):
        self.add_update_values(values)
        for offset in range(0, len(pk_list), GET_ITERATOR_CHUNK_SIZE):
            self.clear_where()
            self.add_filter(
                "pk__in", pk_list[offset : offset + GET_ITERATOR_CHUNK_SIZE]
            )
            self.get_compiler(using).execute_sql(NO_RESULTS)