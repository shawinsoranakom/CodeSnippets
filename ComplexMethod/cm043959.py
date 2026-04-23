def _extract_indicator_metadata(
        self, dimension_group_attrs: dict, structure: dict
    ) -> dict:
        """Extract indicator metadata from dimensionGroupAttributes."""
        indicator_metadata: dict = {}

        # Get the dimensionGroup attribute definitions from structure
        dim_group_defs = structure.get("attributes", {}).get("dimensionGroup", [])

        # Create index maps for each attribute type
        attr_index_map: dict = {}
        for i, attr_def in enumerate(dim_group_defs):
            attr_index_map[attr_def.get("id")] = i

        indicator_dim = None
        indicator_dim_position = None
        series_dims = structure.get("dimensions", {}).get("series", [])

        # List of possible indicator dimension names
        indicator_candidates = [
            "INDICATOR",
            "COICOP_1999",
            "PRODUCTION_INDEX",
            "ACTIVITY",
            "PRODUCT",
            "SERIES",
            "ITEM",
        ]

        for i, dim in enumerate(series_dims):
            dim_id = dim.get("id")
            if dim_id in indicator_candidates or "INDICATOR" in dim_id:
                indicator_dim = dim
                indicator_dim_position = i
                break

        if not indicator_dim or indicator_dim_position is None:
            return indicator_metadata

        for group_key, attr_values in dimension_group_attrs.items():
            # Parse the group key to get the indicator index
            # The key format is like ":0:::" where positions correspond to series dimensions
            key_cleaned = group_key.strip(":")
            key_parts = key_cleaned.split(":") if key_cleaned else []

            # Ensure we have enough parts
            if len(key_parts) > indicator_dim_position:
                indicator_idx_str = key_parts[indicator_dim_position]
            else:
                continue

            if not indicator_idx_str:
                continue

            try:
                indicator_idx = int(indicator_idx_str)
            except ValueError:
                continue

            if indicator_idx >= len(indicator_dim.get("values", [])):
                continue

            indicator_code = indicator_dim["values"][indicator_idx].get("id")
            # Extract attribute values
            metadata_entry: dict = {}

            # Parse each attribute value
            for attr_id, attr_idx in attr_index_map.items():
                if attr_idx < len(attr_values):
                    value = attr_values[attr_idx]

                    if attr_id == "SERIES_NAME" and value:
                        # Extract series name directly from the list
                        if isinstance(value, list) and value:
                            metadata_entry["series_name"] = (
                                value[0] if isinstance(value[0], str) else ""
                            )
                    elif attr_id == "TRADE_FLOW" and value is not None:
                        # Get trade flow code and translate using cached codelist
                        if isinstance(value, int):
                            trade_flow_values = dim_group_defs[attr_idx].get(
                                "values", []
                            )
                            if value < len(trade_flow_values):
                                trade_flow_code = trade_flow_values[value].get("id")
                                # Translate using CL_TRADE_FLOW from cache
                                if (
                                    trade_flow_code
                                    and "CL_TRADE_FLOW" in self.metadata._codelist_cache
                                ):
                                    metadata_entry["trade_flow"] = (
                                        self.metadata._codelist_cache[
                                            "CL_TRADE_FLOW"
                                        ].get(trade_flow_code, trade_flow_code)
                                    )
                                elif trade_flow_code:
                                    metadata_entry["trade_flow"] = trade_flow_code
                    elif attr_id == "VALUATION" and value is not None:
                        # Get valuation code and translate if codelist exists
                        if isinstance(value, int):
                            valuation_values = dim_group_defs[attr_idx].get(
                                "values", []
                            )
                            if value < len(valuation_values):
                                valuation_code = valuation_values[value].get("id")
                                # Try to translate using cached codelist
                                if (
                                    valuation_code
                                    and "CL_VALUATION" in self.metadata._codelist_cache
                                ):
                                    metadata_entry["valuation"] = (
                                        self.metadata._codelist_cache[
                                            "CL_VALUATION"
                                        ].get(valuation_code, valuation_code)
                                    )
                                elif valuation_code:
                                    metadata_entry["valuation"] = valuation_code
                    elif attr_id == "UNIT" and value is not None:
                        if isinstance(value, int):
                            unit_values = dim_group_defs[attr_idx].get("values", [])
                            if value < len(unit_values):
                                unit_code = unit_values[value].get("id")
                                # Skip translation for special aggregate codes that
                                # conflict with currency codes
                                special_aggregate_codes = {"ALL", "W0", "W1", "W2"}
                                if unit_code in special_aggregate_codes:
                                    metadata_entry["unit"] = unit_code
                                elif (
                                    unit_code
                                    and "CL_UNIT" in self.metadata._codelist_cache
                                ):
                                    translated_unit = self.metadata._codelist_cache[
                                        "CL_UNIT"
                                    ].get(unit_code, unit_code)
                                    metadata_entry["unit"] = translated_unit
                                else:
                                    metadata_entry["unit"] = unit_code
                    elif attr_id == "TOPIC" and value is not None:
                        # Extract topics - handle both integer indices and direct values
                        topic_codes: list = []

                        # Value is an integer index into the topic values array
                        if isinstance(value, int):
                            topic_values = dim_group_defs[attr_idx].get("values", [])
                            if value < len(topic_values):
                                topic_val = topic_values[value]
                                if isinstance(topic_val, dict):
                                    # Could be {'id': 'F10_I'} or {'ids': ['L81', 'F10_I', 'F10_E']}
                                    if "id" in topic_val:
                                        topic_codes.append(topic_val["id"])
                                    elif "ids" in topic_val:
                                        topic_codes.extend(topic_val["ids"])

                        # Translate topic codes to names using cached codelist
                        topics: list = []
                        if topic_codes and "CL_TOPIC" in self.metadata._codelist_cache:
                            for code in topic_codes:
                                topic_name = self.metadata._codelist_cache[
                                    "CL_TOPIC"
                                ].get(code, code)
                                topics.append(topic_name)
                        elif topic_codes:
                            topics = topic_codes

                        metadata_entry["topic"] = topics
                    elif (
                        attr_id == "KEY_INDICATOR"
                        and value
                        and isinstance(value, list)
                        and value
                    ):
                        metadata_entry["key_indicator"] = (
                            value[0] == "true" if isinstance(value[0], str) else False
                        )

            indicator_metadata[indicator_code] = metadata_entry

        return indicator_metadata