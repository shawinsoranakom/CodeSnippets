def get_related_string_pairs(
        self, query_text: str, n_results: int, threshold: Union[int, float]
    ) -> List[Tuple[str, str, float]]:
        """
        Retrieves up to n string pairs that are related to the given query text within the specified distance threshold.
        """
        string_pairs_with_distances: List[Tuple[str, str, float]] = []
        if n_results > len(self.uid_text_dict):
            n_results = len(self.uid_text_dict)
        if n_results > 0:
            results: QueryResult = self.vec_db.query(query_texts=[query_text], n_results=n_results)
            num_results = len(results["ids"][0])
            for i in range(num_results):
                uid = results["ids"][0][i]
                input_text = results["documents"][0][i] if results["documents"] else ""
                distance = results["distances"][0][i] if results["distances"] else 0.0
                if distance < threshold:
                    input_text_2, output_text = self.uid_text_dict[uid]
                    assert input_text == input_text_2
                    self.logger.debug(
                        "\nINPUT-OUTPUT PAIR RETRIEVED FROM VECTOR DATABASE:\n  INPUT1\n    {}\n  OUTPUT\n    {}\n  DISTANCE\n    {}".format(
                            input_text, output_text, distance
                        )
                    )
                    string_pairs_with_distances.append((input_text, output_text, distance))
        return string_pairs_with_distances