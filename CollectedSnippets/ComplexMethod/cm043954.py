def validate_dimension_constraints(self, dataflow: str, **kwargs) -> None:
        """
        Validate that the provided dimension parameter combinations are valid according
        to IMF API constraints. Uses progressive constraint checking to ensure the
        parameters are actually available for the dataflow.

        Parameters
        ----------
        dataflow : str
            The dataflow ID
        **kwargs
            Dimension parameters to validate

        Raises
        ------
        ValueError
            If the parameter combination is invalid according to API constraints
        """
        # pylint: disable=import-outside-toplevel
        from openbb_core.app.model.abstract.warning import OpenBBWarning
        from openbb_imf.utils.progressive_helper import ImfParamsBuilder

        try:
            builder = ImfParamsBuilder(dataflow)
            dimensions_in_order = builder._get_dimensions_in_order()

            # Build up selections progressively and validate each step
            for dim_id in dimensions_in_order:
                if dim_id in kwargs:
                    user_value = kwargs[dim_id]

                    # Normalize to list for checking
                    # Handle comma-separated or plus-separated strings
                    if isinstance(user_value, str):
                        if "," in user_value:
                            user_values = [v.strip() for v in user_value.split(",")]
                        elif "+" in user_value:
                            user_values = [v.strip() for v in user_value.split("+")]
                        else:
                            user_values = [user_value]
                    elif isinstance(user_value, list):
                        user_values = user_value
                    else:
                        user_values = [user_value] if user_value else []

                    # Filter out empty strings
                    user_values = [v for v in user_values if v]

                    if not user_values:
                        continue

                    # Skip wildcards - they're always valid
                    if user_values == ["*"] or len("+".join(user_values)) > 2000:
                        builder.set_dimension((dim_id, "*"))
                        continue

                    # Get available options for this dimension given prior selections
                    available_options = builder.get_options_for_dimension(dim_id)
                    available_values = {opt["value"] for opt in available_options}

                    # Check if user's values are valid
                    invalid_values = []
                    for val in user_values:
                        if val != "*" and val not in available_values:
                            invalid_values.append(val)

                    if invalid_values:
                        # Build helpful error message
                        prior_selections = {
                            d: kwargs.get(d)
                            for d in dimensions_in_order
                            if d in kwargs
                            and dimensions_in_order.index(d)
                            < dimensions_in_order.index(dim_id)
                        }

                        # Show all available values without truncation
                        all_values = sorted(available_values)
                        error_msg = (
                            f"Invalid value(s) for dimension '{dim_id}': {invalid_values}. "
                            f"Given prior selections {prior_selections}, "
                            f"available values are: {all_values}"
                        )
                        raise ValueError(error_msg)

                    # Set the valid value to progress the builder
                    builder.set_dimension((dim_id, user_values[0]))

            # Check time period constraints from the last dimension validation
            # The _last_constraints_response already contains contentConstraints with TIME_PERIOD info
            start_date = kwargs.get("start_date")
            end_date = kwargs.get("end_date")

            if start_date or end_date:
                constraints = builder._last_constraints_response
                if constraints:
                    full_response = constraints.get("full_response", {})
                    data = full_response.get("data", {})

                    # Time period annotations can be in contentConstraints or dataConstraints
                    # Check both places
                    time_start = None
                    time_end = None

                    # Try contentConstraints first (primary location)
                    content_constraints = data.get("contentConstraints", [])
                    for constraint in content_constraints:
                        for annotation in constraint.get("annotations", []):
                            ann_id = annotation.get("id", "")
                            ann_title = annotation.get("title", "")
                            if ann_id == "time_period_start":
                                time_start = ann_title
                            elif ann_id == "time_period_end":
                                time_end = ann_title

                    # Fall back to dataConstraints if not found
                    if not (time_start and time_end):
                        data_constraints = data.get("dataConstraints", [])
                        for constraint in data_constraints:
                            for annotation in constraint.get("annotations", []):
                                ann_id = annotation.get("id", "")
                                ann_title = annotation.get("title", "")
                                if ann_id == "time_period_start":
                                    time_start = ann_title
                                elif ann_id == "time_period_end":
                                    time_end = ann_title

                    if time_start and time_end:
                        # Use >= because time_end represents the END of the last period
                        # e.g., time_end=2025-01-01 means data up to end of 2024
                        # So start_date=2025-01-01 would be requesting data AFTER the available range
                        if start_date and start_date >= time_end:
                            raise ValueError(
                                f"Requested start_date '{start_date}' is after the latest available data '{time_end}'. "
                                f"Available date range: {time_start} to {time_end}"
                            )
                        if end_date and end_date <= time_start:
                            raise ValueError(
                                f"Requested end_date '{end_date}' is before the earliest available data '{time_start}'. "
                                f"Available date range: {time_start} to {time_end}"
                            )

        except KeyError as e:
            # Dataflow not found or other metadata issue - let it pass through
            warnings.warn(
                f"Could not validate constraints for dataflow '{dataflow}': {e}",
                OpenBBWarning,
            )