def build_filter(self, args: dict, filter_settings: list) -> dict:
        """Build filter dictionary for Astra DB query.

        Args:
            args: Dictionary of arguments from the tool
            filter_settings: List of filter settings from tools_params_v2
        Returns:
            Dictionary containing the filter conditions
        """
        filters = {**self.static_filters}

        for key, value in args.items():
            # Skip search_query as it's handled separately
            if key == "search_query":
                continue

            filter_setting = next((x for x in filter_settings if x["name"] == key), None)
            if filter_setting and value is not None:
                field_name = filter_setting["attribute_name"] if filter_setting["attribute_name"] else key
                filter_key = field_name if not filter_setting["metadata"] else f"metadata.{field_name}"
                if filter_setting["operator"] == "$exists":
                    filters[filter_key] = {**filters.get(filter_key, {}), filter_setting["operator"]: True}
                elif filter_setting["operator"] in ["$in", "$nin", "$all"]:
                    filters[filter_key] = {
                        **filters.get(filter_key, {}),
                        filter_setting["operator"]: value.split(",") if isinstance(value, str) else value,
                    }
                elif filter_setting["is_timestamp"] == True:  # noqa: E712
                    try:
                        filters[filter_key] = {
                            **filters.get(filter_key, {}),
                            filter_setting["operator"]: self.parse_timestamp(value),
                        }
                    except ValueError as e:
                        msg = f"Error parsing timestamp: {e} - Use the prompt to specify the date in the correct format"
                        logger.error(msg)
                        raise ValueError(msg) from e
                else:
                    filters[filter_key] = {**filters.get(filter_key, {}), filter_setting["operator"]: value}
        return filters