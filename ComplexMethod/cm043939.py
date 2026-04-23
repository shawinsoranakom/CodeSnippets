def list_all_dataflow_tables(self) -> dict[str, list[dict]]:
        """
        Get a mapping of all dataflows to their available presentation tables.

        Returns a curated list of validated dataflow/table combinations that
        are known to work correctly with the IMF API.

        Returns
        -------
        dict[str, list[dict]]
            Mapping of dataflow IDs to their available hierarchies.
        """
        # pylint: disable=import-outside-toplevel
        from openbb_imf.utils.constants import (
            PRESENTATION_TABLES,
        )

        result: dict[str, list[dict]] = {}

        for friendly_name, table_spec in PRESENTATION_TABLES.items():
            # Parse the table spec: "DATAFLOW_ID::HIERARCHY_ID" or "DATAFLOW_ID::HIERARCHY_ID:SPLIT_CODE"
            parts = table_spec.split("::")
            if len(parts) != 2:
                continue

            dataflow_id = parts[0]
            table_id = parts[1]

            if dataflow_id not in self.dataflows:
                continue

            try:
                # Get all hierarchies for this dataflow
                all_hierarchies = self.get_dataflow_hierarchies(dataflow_id)
                if not all_hierarchies:
                    continue

                # Find the matching hierarchy
                matching_hierarchy = None
                for h in all_hierarchies:
                    if h.get("id") == table_id:
                        matching_hierarchy = h
                        break

                if matching_hierarchy:
                    # Add friendly_name to the hierarchy info
                    hierarchy_with_name = matching_hierarchy.copy()
                    hierarchy_with_name["friendly_name"] = friendly_name
                    hierarchy_with_name["dataflow_id"] = dataflow_id

                    if dataflow_id not in result:
                        result[dataflow_id] = []
                    result[dataflow_id].append(hierarchy_with_name)
            except Exception:  # noqa: S110  # pylint: disable=broad-exception-caught
                pass

        return result