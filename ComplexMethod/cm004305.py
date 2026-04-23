def _get_numeric_relations(self, question, column_ids, row_ids, table):
        """
        Returns numeric relations embeddings

        Args:
            question: Question object.
            column_ids: Maps word piece position to column id.
            row_ids: Maps word piece position to row id.
            table: The table containing the numeric cell values.
        """

        numeric_relations = [0] * len(column_ids)

        # first, we add any numeric value spans to the question:
        # Create a dictionary that maps a table cell to the set of all relations
        # this cell has with any value in the question.
        cell_indices_to_relations = collections.defaultdict(set)
        if question is not None and table is not None:
            for numeric_value_span in question.numeric_spans:
                for value in numeric_value_span.values:
                    for column_index in range(len(table.columns)):
                        table_numeric_values = self._get_column_values(table, column_index)
                        sort_key_fn = self._get_numeric_sort_key_fn(table_numeric_values, value)
                        if sort_key_fn is None:
                            continue
                        for row_index, cell_value in table_numeric_values.items():
                            relation = get_numeric_relation(value, cell_value, sort_key_fn)
                            if relation is not None:
                                cell_indices_to_relations[column_index, row_index].add(relation)

        # For each cell add a special feature for all its word pieces.
        for (column_index, row_index), relations in cell_indices_to_relations.items():
            relation_set_index = 0
            for relation in relations:
                assert relation.value >= Relation.EQ.value
                relation_set_index += 2 ** (relation.value - Relation.EQ.value)
            for cell_token_index in self._get_cell_token_indexes(column_ids, row_ids, column_index, row_index):
                numeric_relations[cell_token_index] = relation_set_index

        return numeric_relations