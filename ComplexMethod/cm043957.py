def _extract_dataset_attributes(
        self, structure: dict, json_data: dict, dataflow: str
    ) -> dict:
        """Extract dataset-level attributes."""
        dataset_attrs: dict = {}
        # Add dataflow info
        dataflow_obj = self.metadata.dataflows.get(dataflow, {})
        dataset_attrs["dataflow_id"] = dataflow
        dataset_attrs["dataflow_name"] = dataflow_obj.get("name", dataflow)
        dataset_attrs["dataflow_description"] = dataflow_obj.get("description", "")
        # Get dataset attributes from the cached dataflow object
        # These are stored in the dataflow metadata, not in the API response
        for attr_key in [
            "publisher",
            "department",
            "contact_point",
            "keywords",
            "license",
            "suggested_citation",
            "short_source_citation",
            "full_source_citation",
            "publication_date",
            "update_date",
            "methodology_notes",
            "topic_dataset",
            "keywords_dataset",
        ]:
            if attr_key in dataflow_obj:
                dataset_attrs[attr_key] = dataflow_obj.get(attr_key)

        # Extract attributes from structure response (for UPDATE_DATE, PUBLICATION_DATE, etc.)``
        if "attributes" in structure and "dataSet" in structure["attributes"]:
            dataset_attributes = []
            if "dataSets" in json_data and json_data["dataSets"]:
                dataset_attributes = json_data["dataSets"][0].get("attributes", [])

            # If no attributes in the response, return what we have from cache
            if not dataset_attributes:
                return dataset_attrs

            attr_defs = structure["attributes"]["dataSet"]

            # Iterate through both definitions and values together by index
            for i, attr_def in enumerate(attr_defs):
                attr_id = attr_def.get("id")

                if attr_id not in [
                    "CONTACT_POINT",
                    "PUBLISHER",
                    "DEPARTMENT",
                    "LICENSE",
                    "SUGGESTED_CITATION",
                    "SHORT_SOURCE_CITATION",
                    "FULL_SOURCE_CITATION",
                    "PUBLICATION_DATE",
                    "UPDATE_DATE",
                    "METHODOLOGY_NOTES",
                    "TOPIC_DATASET",
                    "KEYWORDS_DATASET",
                ]:
                    continue

                attr_value = (
                    dataset_attributes[i] if i < len(dataset_attributes) else None
                )

                if attr_value is not None and attr_value != [None]:
                    if attr_id == "TOPIC_DATASET":
                        topic_codes = []
                        if isinstance(attr_value, int) and "values" in attr_def:
                            values_list = attr_def.get("values", [])
                            if attr_value < len(values_list):
                                topic_val = values_list[attr_value]
                                if isinstance(topic_val, dict):
                                    if "ids" in topic_val:
                                        topic_codes.extend(topic_val.get("ids", []))
                                    elif "id" in topic_val:
                                        topic_codes.append(topic_val.get("id"))
                                else:
                                    topic_codes.append(topic_val)
                        elif isinstance(attr_value, list):
                            for val in attr_value:
                                if isinstance(val, int) and "values" in attr_def:
                                    values_list = attr_def.get("values", [])
                                    if val < len(values_list):
                                        topic_val = values_list[val]
                                        if isinstance(topic_val, dict):
                                            if "ids" in topic_val:
                                                topic_codes.extend(
                                                    topic_val.get("ids", [])
                                                )
                                            elif "id" in topic_val:
                                                topic_codes.append(topic_val.get("id"))
                                        else:
                                            topic_codes.append(topic_val)
                                elif isinstance(val, str):
                                    topic_codes.append(val)

                        # Translate topic codes to names using cached codelist
                        if topic_codes and "CL_TOPIC" in self.metadata._codelist_cache:
                            topic_names = []
                            for code in topic_codes:
                                topic_name = self.metadata._codelist_cache[
                                    "CL_TOPIC"
                                ].get(code, code)
                                topic_names.append(topic_name)
                            dataset_attrs["topics"] = topic_names
                        elif topic_codes:
                            dataset_attrs["topics"] = topic_codes

                    elif attr_id == "KEYWORDS_DATASET":
                        keywords = self._extract_attribute_value(attr_value, attr_def)
                        if keywords:
                            dataset_attrs["keywords"] = keywords
                    elif attr_id == "UPDATE_DATE":
                        date_value = self._extract_attribute_value(attr_value, attr_def)
                        if date_value:
                            try:
                                if isinstance(date_value, str) and "." in date_value:
                                    parts = date_value.split(".")
                                    if len(parts) == 2:
                                        fractional = parts[1][:6].ljust(6, "0")
                                        date_value = f"{parts[0]}.{fractional}Z"
                                dataset_attrs["last_updated"] = date_value
                            except (  # noqa  # pylint: disable=broad-exception-caught
                                Exception
                            ):
                                dataset_attrs["last_updated"] = date_value
                    elif attr_id == "PUBLICATION_DATE":
                        pub_date = self._extract_attribute_value(attr_value, attr_def)
                        if pub_date:
                            dataset_attrs["publication_date"] = pub_date
                    else:
                        final_value = self._extract_attribute_value(
                            attr_value, attr_def
                        )
                        if final_value:
                            dataset_attrs[attr_id.lower()] = final_value

        return dataset_attrs