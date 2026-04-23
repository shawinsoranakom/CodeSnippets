def _find_answer_ids_from_answer_texts(
        self,
        column_ids,
        row_ids,
        tokenized_table,
        answer_texts,
    ):
        """Maps question with answer texts to the first matching token indexes."""
        answer_ids = [0] * len(column_ids)
        for answer_text in answer_texts:
            for coordinates in self._find_answer_coordinates_from_answer_text(
                tokenized_table,
                answer_text,
            ):
                # Maps answer coordinates to indexes this can fail if tokens / rows have
                # been pruned.
                indexes = list(
                    self._get_cell_token_indexes(
                        column_ids,
                        row_ids,
                        column_id=coordinates.column_index,
                        row_id=coordinates.row_index - 1,
                    )
                )
                indexes.sort()
                coordinate_answer_ids = []
                if indexes:
                    begin_index = coordinates.token_index + indexes[0]
                    end_index = begin_index + len(answer_text)
                    for index in indexes:
                        if index >= begin_index and index < end_index:
                            coordinate_answer_ids.append(index)
                if len(coordinate_answer_ids) == len(answer_text):
                    for index in coordinate_answer_ids:
                        answer_ids[index] = 1
                    break
        return answer_ids