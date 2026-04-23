def search_dataflows(self, query: str) -> list[dict]:
        """Search dataflows based on a query string.

        Parameters
        ----------
        query : str
            The search query string, which can include AND (+) and OR (|) operators,
            as well as quoted phrases for exact matches.
        Returns
        -------
        list[dict]
            A list of matching dataflows, grouped by their structureRef ID.
        """
        grouped_results: dict = {}
        parsed_query = self._parse_query(query)

        if not parsed_query:
            raise OpenBBError(
                ValueError(f"Query string is empty or invalid -> '{query}'")
            )

        for dataflow_obj in self.dataflows.values():
            dataflow_id = dataflow_obj.get("id", "").lower()
            dataflow_name = dataflow_obj.get("name", "").lower()
            dataflow_description = dataflow_obj.get("description", "").lower()
            dataflow_matches = False

            for or_group in parsed_query:
                or_group_matches_all_and_terms = True

                for and_term in or_group:
                    if not (
                        and_term in dataflow_id
                        or and_term in dataflow_name
                        or and_term in dataflow_description
                    ):
                        or_group_matches_all_and_terms = False
                        break

                if or_group_matches_all_and_terms:
                    dataflow_matches = True
                    break

            if dataflow_matches:
                structure_ref_id = dataflow_obj.get("structureRef", {}).get("id")
                if structure_ref_id:
                    if structure_ref_id not in grouped_results:
                        grouped_results[structure_ref_id] = []

                    grouped_results[structure_ref_id].append(
                        {
                            "id": dataflow_obj.get("id"),
                            "name": dataflow_obj.get("name"),
                            "description": dataflow_obj.get("description", ""),
                        }
                    )

        final_results = [
            {"group_id": group_id, "dataflows": dataflows}
            for group_id, dataflows in grouped_results.items()
        ]

        return final_results